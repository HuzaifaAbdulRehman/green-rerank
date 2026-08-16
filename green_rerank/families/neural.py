"""Neural families.

Two, deliberately, because they answer different questions:

``multvae``
    Denoising variational autoencoder over the interaction vector (Liang et al., 2018).
    Matrix-based, so it needs no interaction order. Chosen because MultiVAE is in the
    model set of the work this project is measured against (Wegmeth et al., ACM TORS
    2025), which makes our cost figures comparable to published ones rather than
    free-floating.

``gru4rec``
    Session-based recurrent model (Hidasi et al., 2016). Sequential, and the family
    closest to the supervisor's own published direction -- semantically enhanced
    sequential recommendation for e-commerce.

Both are **work-bounded**: they run a fixed number of epochs and stop. No early stopping
on wall-clock, and no convergence check that would let a faster machine train a better
model. That matters more here than in an accuracy paper: if the stopping rule depends on
machine speed, then training cost and model quality both become properties of the
hardware, and every cost comparison silently becomes a benchmark of the CPU.

torch is an optional dependency (~2.5 GB). The network classes are therefore constructed
inside :meth:`fit` rather than at module scope, so this module imports on a machine that
has never seen torch and the failure, when it comes, is a sentence rather than a
traceback.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from green_rerank.families.base import Family, Sequences

try:  # pragma: no cover - import guard
    import torch

    _HAS_TORCH = True
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    _HAS_TORCH = False


TORCH_MISSING = (
    "this family needs PyTorch, which is an optional dependency because it is ~2.5 GB "
    "and the rest of the project runs without it. Install it with:\n"
    "    pip install -e .[neural]\n"
    "or, for the CPU-only build:\n"
    "    pip install torch --index-url https://download.pytorch.org/whl/cpu"
)


def torch_available() -> bool:
    """Whether the neural families can run here."""
    return _HAS_TORCH


class _TorchFamily(Family):
    """Shared plumbing: seeding, device choice, and deterministic training.

    Deliberately CPU-only unless a GPU is explicitly requested. The development machine
    has integrated graphics and no CUDA, and silently falling back between devices would
    make cost figures incomparable between runs on the same code -- the single most
    important thing to prevent in a project whose output is a cost table.
    """

    def __init__(self, epochs: int = 20, batch_size: int = 128, seed: int = 0, device: str = "cpu"):
        super().__init__()
        if not _HAS_TORCH:
            raise ImportError(TORCH_MISSING)
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.device = device
        self._net = None

    iterative = True

    def _seed_everything(self) -> None:
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        # Deterministic algorithms where torch offers them: two runs of the same
        # configuration must produce the same model, or repeated-seed cost studies
        # measure run-to-run drift alongside the thing being varied.
        torch.use_deterministic_algorithms(True, warn_only=True)

    @property
    def model_bytes(self) -> int:
        if self._net is None:
            return 0
        return int(sum(p.numel() * p.element_size() for p in self._net.parameters()))


# ------------------------------------------------------------------------ MultVAE


class MultVAE(_TorchFamily):
    """Variational autoencoder with a multinomial likelihood.

    The likelihood is the part that matters and the part usually got wrong. A user's
    interaction vector is a *count* over a fixed budget of attention, not a set of
    independent coin flips, so the multinomial log-likelihood is the right fit and a
    per-item binary cross-entropy is not. Liang et al. report the difference as large.
    """

    name = "multvae"
    needs_sequences = False

    def __init__(
        self,
        latent: int = 64,
        hidden: int = 300,
        epochs: int = 20,
        batch_size: int = 128,
        learning_rate: float = 1e-3,
        dropout: float = 0.5,
        beta: float = 0.2,
        seed: int = 0,
        device: str = "cpu",
    ) -> None:
        super().__init__(epochs=epochs, batch_size=batch_size, seed=seed, device=device)
        self.latent = latent
        self.hidden = hidden
        self.learning_rate = learning_rate
        self.dropout = dropout
        # Fixed rather than annealed. Annealing beta over training makes the model's
        # quality depend on the epoch budget in a way that would confound the cost
        # comparison: more epochs would buy both more training and a different
        # objective, and the two could not be separated afterwards.
        self.beta = beta

    def _build(self, n_items: int):
        from torch import nn

        class Net(nn.Module):
            def __init__(self, n_items, hidden, latent, dropout):
                super().__init__()
                self.drop = nn.Dropout(dropout)
                self.encode = nn.Sequential(nn.Linear(n_items, hidden), nn.Tanh())
                # One head emitting both mean and log-variance, as in the paper.
                self.to_latent = nn.Linear(hidden, latent * 2)
                self.decode = nn.Sequential(
                    nn.Linear(latent, hidden), nn.Tanh(), nn.Linear(hidden, n_items)
                )
                self.latent = latent

            def forward(self, x):
                # L2-normalise then drop: the paper's denoising step. Normalising after
                # dropout would let the scale of the input depend on how many entries
                # happened to survive.
                h = torch.nn.functional.normalize(x, p=2, dim=1)
                h = self.drop(h)
                stats = self.to_latent(self.encode(h))
                mu, logvar = stats[:, : self.latent], stats[:, self.latent :]
                if self.training:
                    std = torch.exp(0.5 * logvar)
                    z = mu + std * torch.randn_like(std)
                else:
                    # No sampling at serving time: recommendations must be
                    # reproducible, and the mean is the model's actual belief.
                    z = mu
                return self.decode(z), mu, logvar

        return Net(n_items, self.hidden, self.latent, self.dropout)

    def fit(self, matrix: sparse.csr_matrix, sequences: Sequences | None = None) -> MultVAE:
        self._seed_everything()
        n_users, n_items = matrix.shape
        self._net = self._build(n_items).to(self.device)
        optimiser = torch.optim.Adam(self._net.parameters(), lr=self.learning_rate)

        matrix = matrix.tocsr().astype(np.float32)
        order = np.arange(n_users)
        rng = np.random.default_rng(self.seed)

        self._net.train()
        for _ in range(self.epochs):
            rng.shuffle(order)
            for start in range(0, n_users, self.batch_size):
                rows = order[start : start + self.batch_size]
                batch = torch.from_numpy(matrix[rows].toarray()).to(self.device)

                logits, mu, logvar = self._net(batch)
                log_probability = torch.log_softmax(logits, dim=1)
                # Multinomial likelihood: reward probability mass placed on the items
                # the user actually interacted with.
                reconstruction = -(log_probability * batch).sum(dim=1).mean()
                divergence = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).sum(dim=1).mean()

                loss = reconstruction + self.beta * divergence
                optimiser.zero_grad()
                loss.backward()
                optimiser.step()

        self._net.eval()
        self._n_items = n_items
        self._fitted = True
        return self

    def _scores(self, matrix: sparse.csr_matrix, user_rows: np.ndarray) -> np.ndarray:
        batch = torch.from_numpy(matrix[user_rows].toarray().astype(np.float32)).to(self.device)
        with torch.no_grad():
            logits, _, _ = self._net(batch)
        return logits.cpu().numpy()


# ------------------------------------------------------------------------ GRU4Rec


class GRU4Rec(_TorchFamily):
    """Session-based recommendation with a recurrent encoder.

    Item ids are shifted by one so that index 0 can be a padding token. Getting this
    wrong is the classic bug in sequence models: without a reserved pad the network
    learns that "item 0" appears at the start of every short session, and the resulting
    model looks trained and is quietly wrong about the most popular item in the
    catalogue.
    """

    name = "gru4rec"
    needs_sequences = True

    def __init__(
        self,
        hidden: int = 64,
        embedding: int = 64,
        epochs: int = 20,
        batch_size: int = 64,
        learning_rate: float = 1e-3,
        max_length: int = 50,
        seed: int = 0,
        device: str = "cpu",
    ) -> None:
        super().__init__(epochs=epochs, batch_size=batch_size, seed=seed, device=device)
        self.hidden = hidden
        self.embedding = embedding
        self.learning_rate = learning_rate
        self.max_length = max_length
        self._sequences: Sequences | None = None

    def _build(self, n_items: int):
        from torch import nn

        class Net(nn.Module):
            def __init__(self, n_items, embedding, hidden):
                super().__init__()
                # +1 for the pad token at index 0.
                self.embed = nn.Embedding(n_items + 1, embedding, padding_idx=0)
                self.gru = nn.GRU(embedding, hidden, batch_first=True)
                self.out = nn.Linear(hidden, n_items)

            def forward(self, batch, lengths):
                hidden_states, _ = self.gru(self.embed(batch))
                # Take the state at each session's true final position, not at the end
                # of the padded tensor -- otherwise every short session is read off
                # after a run of pad tokens and the model is scored on padding.
                index = (lengths - 1).clamp(min=0).view(-1, 1, 1)
                index = index.expand(-1, 1, hidden_states.size(2))
                final = hidden_states.gather(1, index).squeeze(1)
                return self.out(final)

        return Net(n_items, self.embedding, self.hidden)

    def _training_pairs(self, sequences: Sequences, n_items: int):
        """Every prefix of every session, paired with the item that followed it.

        One session of length L yields L-1 training examples rather than one. Using only
        the final item would discard most of the signal in an already small dataset.
        """
        inputs: list[list[int]] = []
        targets: list[int] = []
        for history in sequences.by_user.values():
            trimmed = history[-(self.max_length + 1) :]
            for cut in range(1, len(trimmed)):
                prefix = trimmed[max(0, cut - self.max_length) : cut]
                inputs.append([item + 1 for item in prefix])  # shift past the pad token
                targets.append(trimmed[cut])
        return inputs, targets

    def _pad(self, rows: list[list[int]]):
        lengths = torch.tensor([max(len(r), 1) for r in rows], dtype=torch.long)
        padded = torch.zeros(len(rows), self.max_length, dtype=torch.long)
        for position, row in enumerate(rows):
            clipped = row[-self.max_length :]
            padded[position, : len(clipped)] = torch.tensor(clipped, dtype=torch.long)
        return padded.to(self.device), lengths.clamp(max=self.max_length).to(self.device)

    def fit(self, matrix: sparse.csr_matrix, sequences: Sequences | None = None) -> GRU4Rec:
        sequences = self._require_sequences(sequences)
        self._seed_everything()
        n_items = matrix.shape[1]

        self._net = self._build(n_items).to(self.device)
        optimiser = torch.optim.Adam(self._net.parameters(), lr=self.learning_rate)
        loss_fn = torch.nn.CrossEntropyLoss()

        inputs, targets = self._training_pairs(sequences, n_items)
        if not inputs:
            raise ValueError("no usable sessions: every user history was shorter than 2 items")

        order = np.arange(len(inputs))
        rng = np.random.default_rng(self.seed)

        self._net.train()
        for _ in range(self.epochs):
            rng.shuffle(order)
            for start in range(0, len(order), self.batch_size):
                picked = order[start : start + self.batch_size]
                batch, lengths = self._pad([inputs[i] for i in picked])
                wanted = torch.tensor([targets[i] for i in picked], dtype=torch.long).to(
                    self.device
                )

                loss = loss_fn(self._net(batch, lengths), wanted)
                optimiser.zero_grad()
                loss.backward()
                optimiser.step()

        self._net.eval()
        # Held for serving: scoring a user means replaying their history, so the model
        # alone is not sufficient. This is a real serving cost that a factor model does
        # not have, and it belongs in the memory figure.
        self._sequences = sequences
        self._n_items = n_items
        self._fitted = True
        return self

    def _scores(self, matrix: sparse.csr_matrix, user_rows: np.ndarray) -> np.ndarray:
        assert self._sequences is not None
        histories = [
            [item + 1 for item in self._sequences.truncated(int(row))] or [0] for row in user_rows
        ]
        batch, lengths = self._pad(histories)
        with torch.no_grad():
            return self._net(batch, lengths).cpu().numpy()


NEURAL: dict[str, type[Family]] = {
    MultVAE.name: MultVAE,
    GRU4Rec.name: GRU4Rec,
}
