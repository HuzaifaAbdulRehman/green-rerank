# Results directories

Each directory is one experiment, self-describing, and produced by one code version.

| directory | what it is |
|-----------|------------|
| `main/` | the primary sweep — 170 runs, 5 catalogues × up to 5 families × {no reranker, `quota_mmr`} × 5 repeats |
| `depth/` | retrieval-depth sensitivity — 90 runs varying the reranker's problem size over 50…800 |
| `energy/` | the same pipeline with the energy meter attached, for the agreement test in report §5.1 |
| `validity/` | the first graded-load experiment — **superseded**, see below |
| `validity_v2/` | the graded-load experiment: what the energy backend reports about a *known* load. Report §5 quotes this one |
| `validity_v2_repeat1/` | an independent repetition of `validity_v2/` on the same idle machine. Kept because the backend's verdict **differs between the two**, which report §5 treats as a result |
| `rerankers/` | the first reranker comparison — **superseded**, see below |
| `rerankers_v2/` | rerankers including `balanced_quota`, the baseline that decides the QUBO question |
| `main_v2/`, `depth_v2/` | regenerated against the corrected companion |
| `depth_pinned/`, `rerankers_pinned/` | `depth_v2/` and `rerankers_v2/` repeated with the thread count pinned, each with predictions registered in its own manifest. Both **confirm** the section they test: §7.6's exponents move by at most 0.02 and §10's parity and diversity results are bit-identical |
| `main_pinned/` | `main_v2/` repeated with `OMP_NUM_THREADS=1`. Tests report §7.1's threading diagnosis against predictions registered in its own manifest before the run. **Not a correction of `main_v2/`** — a second measurement condition; absolute costs are not comparable between them, which is the point |
| `plumbing/` | driver validation only — every row stamped `trustworthy=False`, not a measurement |

## Which directories are current

`main_v2/`, `depth_v2/` and `rerankers_v2/` supersede `main/`, `depth/` and `rerankers/`.
The originals are kept rather than deleted: the difference between them is itself a
measurement. **The reason differs per directory, and only one of them involves the
interaction-matrix defect.**

| superseded | why | can its code state be reconstructed? |
|------------|-----|--------------------------------------|
| `main/` | Companion `binary=True` summed duplicate interactions, so 0.2–18.1 % of training rows on the four Amazon catalogues were counts rather than indicators, and the popularity tiers used as fairness groups counted repeat purchases. Also: the degenerate exposure-parity metric, and accuracy tested on one repeat of five. | **No** — `green_rerank dirty=True` |
| `depth/` | Six depth-800 rows were labelled with a depth they never ran at, because the row assembly overwrote the measured value with the requested one. Also the degenerate parity metric. | **No** — `green_rerank dirty=True` |
| `rerankers/` | It omitted `balanced_quota`, so the annealers were compared against a heuristic with no remainder rule rather than against correct apportionment. Also: both annealers were unseeded, and `lam` differed between the classical (0.5) and QUBO (0.3) solvers, so the two families optimised different objectives. | **No** — `companion dirty=True` |
| `validity/` | Taken at `511d993` against a superseded companion. Two of the claims report §5 drew from it did not reproduce when the experiment was re-run: utilisation is not reliably pinned at exactly 0 %, and the fully loaded run does **not** report less total energy than idle. | **No** — `green_rerank dirty=True` |
| `energy/` | The meter-enabled sweep behind the deleted report §5.1. Its regression may well have been right; it cannot be regenerated, so the section was removed rather than restated. | **No** — `green_rerank dirty=True` |

The three `_pinned` directories do not supersede their `_v2` counterparts. Each pair differs
only in BLAS thread count: the `_v2` run is what the study measures when the unit is left to
its default, the `_pinned` run is the same experiment with the confound removed. Keeping both
halves is what makes the threading diagnosis testable rather than asserted, and every
accuracy figure is bit-identical across each pair — the control proving the intervention
touched cost and nothing else.

`validity_v2/` and `validity_v2_repeat1/` are **both current** — they are two runs of one
experiment, not a replacement and an original. §5 reports the pair because the backend's
pass/fail verdict flips between them on an idle machine, and a single run would have
concealed that. A third run exists in this session's history and is deliberately **not**
kept: it was taken while this project's own mutation suite occupied the machine, so it
records contention rather than the backend.

**The interaction-matrix defect did not affect `depth/` or `rerankers/`.** Both ran on
MovieLens 100K only, which contains zero duplicate `(user, item)` pairs — confirmed from
both sides: this project measured 0 duplicate rows in 98,344, and the companion's density
(0.0773) and item count (1,349) are identical before and after the dedupe fix. Attributing
C2 to those two directories would be wrong, and an earlier version of this file did.

**None of the three superseded directories can have its code state reconstructed**, which
makes them weaker evidence than the `_v2` set. `main/` and `depth/` record
`green_rerank dirty=True`, so this project's own source at measurement time is
unrecoverable; `rerankers/` records `companion dirty=True`, so the solver code is. Every
`_v2` directory records `dirty=False` on both repositories.

## Reproducing each directory

Every sweep needs an idle machine and mains power; the driver refuses otherwise. Runtimes
are measured wall-clock from the committed manifests.

```bash
# main_v2 -- the primary sweep, 170 runs, ~33 min
python -m experiments.sweep --config experiments/configs/main_v2.yaml

# main_pinned -- the same sweep with the thread count pinned, 170 runs, ~24 min
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \n  python -m experiments.sweep --config experiments/configs/main_pinned.yaml

# depth_pinned / rerankers_pinned -- the same two studies, threads pinned, ~4 and ~11 min
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \n  python -m experiments.sweep --config experiments/configs/depth_pinned.yaml
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \n  python -m experiments.sweep --config experiments/configs/rerankers_pinned.yaml

# depth_v2 -- retrieval-depth sensitivity, 90 runs, ~5 min
python -m experiments.sweep --config experiments/configs/depth_v2.yaml

# rerankers_v2 -- all six rerankers incl. balanced_quota, 63 runs, ~12 min
python -m experiments.sweep --config experiments/configs/rerankers_v2.yaml

# validity -- the graded-load energy check, ~2 min, needs no dataset
#   requires `pip install -e ".[energy]"`; the [dev] extra alone does NOT install codecarbon
python -m experiments.validity

# analysis, for each directory
python -m experiments.analyse  --results results/main_v2
python -m experiments.compare  --results results/main_v2 --reference popularity
python -m experiments.figures   --results results/main_v2

# every number any document quotes, regenerated from the raw records
python -m experiments.headline
python -m experiments.verify_claims
```

`experiments/when_idle.py` will hold a sweep until the machine is quiet and then start it:

```bash
python -m experiments.when_idle -- python -m experiments.sweep --config experiments/configs/main_v2.yaml
```

## Files

- **`manifest.json`** — provenance. Revision of **both** repositories (every accuracy
  metric here is computed by companion code, so naming only this one would be half a
  record), package versions, machine, the measured clock quantum, the preflight record,
  and the conditions observed during the run. `dirty` refers to the *code*: results are
  written into the working tree while a sweep runs, so counting them would make the flag
  true in every manifest and useless.
- **`runs.csv`** — one row per run: per-stage costs, derived once/per-request costs,
  accuracy metrics, and the trust flag.
- **`readings.csv`** — the raw measurement windows behind those costs, including repeat
  counts and any energy channels. Kept because `runs.csv` holds *derived* figures; if a
  derivation is ever found wrong — and one already was — these can be reprocessed
  instead of re-running the sweep.
- **`per_user.csv`** — one row per served user, keyed on the user's row index rather than
  its position in the sample, so two runs can be paired correctly for the accuracy tests.
- **`conditions.json`** — power source and CPU frequency sampled *during* the run.
- **`tables/`**, **`figures/`** — generated by `experiments.analyse`, `experiments.compare`
  and `experiments.figures`. Regenerating them is a second; re-running the sweep is an
  hour, which is why the raw files above are kept.

## Reading the trust flag

Every row carries `trustworthy`. A row is marked false when the machine was busy enough
at the start of the sweep that CPU contention would be charged to whatever was being
measured. **`experiments.analyse` refuses to read such rows** unless explicitly
overridden, because a contaminated cost figure is not a slightly worse measurement — it
is a measurement of something else, and it looks entirely ordinary in a table.

All 170 rows in `main/` are trustworthy.
