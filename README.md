# green-rerank

A measurement harness for the **energy cost of a recommender pipeline**, and a study run
with it on commodity hardware.

Existing energy studies of recommender systems report a figure per experimental run.
That figure adds a cost paid **once** to a cost paid **per request**, and the sum answers
no question a deployer has: a model that trains for an hour then serves nearly free, and
one that trains instantly then burns an hour answering queries, can report the same total
and imply opposite decisions.

This project measures the stages separately, which turns a cost table into

```
C(N) = C_once + N * C_per_request
```

and therefore into a **break-even request volume** — the traffic level at which one model
family stops being the cheaper choice and another starts.

It is the companion to [`feasible-rerank`](https://github.com/HuzaifaAbdulRehman/feasible-rerank),
which studies the reranker as an optimisation problem. This project studies the pipeline
the reranker sits in, and imports that project's metrics, loaders and evaluation
protocol rather than reimplementing them.

---

## What it claims

Three things, chosen because a literature search found each of them unclaimed. The
cross-family energy comparison itself is **not** one of them — Wegmeth et al. (ACM TORS
2025) published 63 algorithms across 14 datasets with a physical power meter, and this
project is measured against that work rather than pretending it does not exist.

**1. Break-even request volume.** Prior work reports energy per run. Nobody reports the
request count at which families cross, which is the form a deployment decision actually
takes.

**2. The reranker as a costed line item.** Prior pipeline decompositions are fit /
predict / evaluate. No published energy study costs a fairness reranker, despite the
fairness-in-ranking literature proposing them steadily.

**3. Whether software energy estimation is valid here.** Reported below, because on this
hardware the answer is no, and that is a result rather than an obstacle.

---

## What it found

170 measured runs across five catalogues (147 to 11,268 items), five model families and
two reranking conditions, five repeats each, plus 90 runs on retrieval depth, 63 on
rerankers, and 323 more repeating all three with the BLAS thread count pinned. Zero
failures, every row passing the trust check on an idle mains-powered machine, no stage
falling below the clock quantum. Full write-up in
[`docs/report.md`](docs/report.md).

An external audit of the first version of this study found six code defects. Everything
below is regenerated against the corrected code, from `results/main_v2/`,
`results/depth_v2/` and `results/rerankers_v2/`. **Three earlier results directories are
superseded and must not be cited**; `results/README.md` records what was wrong with each.
Several claims are weaker than they were and two are retracted — marked as such, because a
report whose confidence never moves is not evidence of anything.

**A break-even volume is measurable — but only once the cost unit is pinned, and that is the
finding.** Measured the way most studies would, ItemKNN against ALS on MovieLens 100K gives
an interval spanning **123×** with its denominator changing sign across repeats of identical
work: no reportable answer. The cause is the unit. CPU-seconds counts every thread and BLAS
re-picks its thread count per process, so ALS's scoring stage varied 1.38–2.47× in
utilisation while ItemKNN's, single-threaded, held at 1.00.

Pinning the thread count was **pre-registered as a prediction and then tested** — the
predictions are stamped in `results/main_pinned/manifest.json` before the run produced
anything. All five held: ALS's variance collapses to 0.019, the denominator becomes
single-signed in 5 of 5 repeats, and the break-even becomes **N = 48,011 requests, 95 % CI
[41,952 – 52,914]** — a 1.3× interval with 100 % of replicates crossing. Stable pairs go
from 12 of 45 to 13, and the widest stable interval from 7.8× to 2.7×. Accuracy is
bit-identical across both sweeps, so only the cost column moved.

**So: pin `OMP_NUM_THREADS=1` before measuring cost.** Unpinned, GRU4Rec's training reports
414.6–478.0 CPU-seconds; pinned, the same work reports **78.7–80.9** and finishes *faster*
in wall-clock (79–81 s against 104–121 s). The extra 5.4× was threads spin-waiting, charged
as work — so CPU-seconds is not just noisier on parallel stages, it is **biased upward**.

**Fairness reranking is 81.6–97.6 % of per-request cost**, multiplying serving cost 5.7× to
42.8×. A deployer adding exposure fairness to a popularity baseline on MovieLens 100K is
not paying a margin, they are paying **24.9 times** their serving cost. As far as the
literature search found, this is the first published figure for what a fairness reranker
costs as a share of a pipeline.

**That spend does not reliably buy fairness.** On `luxury_beauty` the most expensive
configuration measured — 42.8× serving cost — changed exposure parity for **0 of 1,000
paired user-records**, in either direction. On `software` a comparable multiplier did move
parity, 1.500 → 1.000, while cutting NDCG from 0.0048 to 0.0019. The multiplier is
reliable; the benefit is catalogue-dependent and has to be measured.

**Retrieve shallowly when reranking.** Going from 50 to 800 candidates costs **31.5×** more
in the rerank stage (O(n^1.21–1.29)) and delivers **no** measurable fairness improvement —
parity moves 0.0075–0.0177 across the whole range. The earlier claim that accuracy *falls*
with depth is **retracted** (ρ = −0.115, p = 0.45); the recommendation stands on cost alone.

**On MovieLens 100K, nothing tested beats recommending the most popular items
reproducibly.** ItemKNN, ALS and MultVAE reach significance in 0 of 5 repeats. GRU4Rec
reaches it in **1 of 5** — for 79.4 CPU-seconds of training against popularity's 1.58e-4,
a factor of **502,412** (2.6 million if measured unpinned, inflated by thread spin-wait).
The earlier claim that GRU4Rec beats the baseline there rested on a single repeat.

ML-100K is the **exception**: ItemKNN beats popularity in every repeat on three of the other
four catalogues, and in 4 of 5 repeats on the fourth. A method validated only on ML-100K —
the catalogue everyone uses — can therefore be reported as beating a baseline it does not
beat.

**Retraining cadence is a bigger lever than model choice.** Holding traffic fixed at 100,000
requests, GRU4Rec's total cost moves **801×** between training once and retraining every 100
requests. What that buys was **not measured** and is no longer claimed: no model in any
sweep was retrained on newer data, because the harness has no temporal split to retrain
across.

**A classical reranker matches the quantum-inspired ones exactly, for ~1/270th the cost.**
`balanced_quota` — largest-remainder apportionment — reaches exposure parity 0.200, the
optimum permitted by the integrality of list positions, on all three retrieval families,
and ties both annealers on **900 of 900** paired user-records. This **retracts** the earlier
claim that the annealers reached a fairness optimum classical methods could not; that claim
was an artefact of the correct baseline being missing from the registry. What the annealers
do still buy is list diversity — intra-list similarity 0.286–0.297 against 0.357, better on
893 of 900 users, p < 0.001 — at roughly 250–300× the cost of the stage that already
dominates per-request cost. That range is wide because `balanced_quota`'s stage cost is only
about seven clock ticks, so the ratio's denominator is quantised; an earlier draft's
"288–290×" was false precision inherited from the clock, not a property of the solver.

---

## The cost unit is CPU-seconds, and that is a finding

`codecarbon`'s reported energy **barely moves on the development machine**. Measured on
codecarbon 3.3.0 with a graded load — 0, 1, 2, 4 and 8 busy processes, 20 s each, on a
machine first confirmed idle. Reproduce with `python -m experiments.validity`:

| busy workers | reported CPU power | reported utilisation | reported RAM power | total energy |
|--------------|--------------------|----------------------|--------------------|--------------|
| 0 | 1.522 W | 0 % | 10.000 W | 6.446e-05 kWh |
| 2 | 1.515 W | 0 % | 10.000 W | 6.619e-05 kWh |
| 4 | 1.530 W | 0 % | 10.000 W | 6.726e-05 kWh |
| 8 | 1.659 W | 0 % | 10.000 W | 7.294e-05 kWh |

RAM power is exactly 10.000 W at every level — a hardcoded constant — and it supplies
**81–87 %** of the reported total. Utilisation reads **zero under eight saturated cores**,
the one condition whose true answer is known in advance. The CPU channel does respond,
weakly: mean CPU power moves 1.551 → 2.302 W, a **1.48×** swing against a true dynamic range
of roughly 10× for a 15 W part. Because the constant channel dominates, mean *total* reported
power moves **1.06×** between an idle machine and a saturated one — and the study spans
workloads differing by six orders of magnitude in cost.

**The backend's own verdict is not reproducible.** Run three times, twice on a confirmed-idle
machine, the driver's pass/fail answer *flips*: one idle run reported *"the backend
responded"*, the next *"did not respond to the load"*. The driver keys on whether any channel
moves more than 2× and the CPU channel's per-second rate lands either side of that line
(1.45×, then 1.53×). A controlled test whose verdict is not stable across repetitions is not
delivering a measurement. What *is* stable across all three runs is the part that needs no
threshold: RAM constant at 10.000 W supplying 81–87 % of the total, utilisation at 0 % under
full load, and total reported power moving 1.04–1.06×.

Two claims an earlier version of this section made **did not reproduce** when the test was
re-run at a clean revision, and are withdrawn: the fully loaded run does **not** report less
total energy than idle, and utilisation is not reliably "exactly 0.0 % at every level" (one
run read 5 % at two workers) — erratic and dead are equally unusable. A third claim, a
regression showing the energy column was not even a rescaled clock, has been deleted because
the sweep behind it cannot be regenerated — it was taken with dirty code. The report records
all three.

The machine (Intel i5-8350U, 15 W TDP, Windows 10) exposes no RAPL, and WSL2 does not
help — verified, not assumed: `/sys/class/powercap` exists but is empty and
`/dev/cpu/0/msr` is absent, because the hypervisor does not pass the counters through.

So the primary cost unit is **CPU-seconds**, measured by the kernel, and joules appear
only as an explicit stated conversion — never as a measurement. `Reading.joules()` takes
a required watts-per-CPU-second argument and has no default, so a joule figure cannot
appear in output without its assumption visible beside it.

This does not weaken the break-even claim. `C(N)` is linear, so a crossover computed in
CPU-seconds is the *same request count* as one computed in joules, provided the
conversion is a constant.

---

## Four measurement traps, and what the code does about them

Each of these was found the hard way, in this project or its companion. They share a
failure mode: **the run completes, the table looks entirely normal, and only the cost
column is wrong.**

**1. The energy probe is not free.** `EmissionsTracker.start()` interrogates the hardware
for seconds. Timing from before it charged that constant to whatever was being measured —
one baseline read 5.4 s for 0.008 s of real work. `MeasurementSession.window` starts the
clock strictly *after* the probe and stops it strictly *before* teardown.

**2. Scoring must be outside the window.** Metric computation is O(k²) per user in pure
Python: noise against a training run, and the *majority* of the reading against a cheap
retrieval. `Stage` has no `SCORE` member at all, so no call site can pass one to a
measured window even by accident.

**3. The clock is 15.625 ms, not 100 ns.** `time.get_clock_info("process_time")` reports
100 ns. The true quantum is the scheduler tick, five orders of magnitude coarser, so a
3 ms stage reads either `0.0` or `0.0156` and two stages differing tenfold can report the
same number. `measure_repeated` repeats the work until the window spans ~20 quanta and
divides; readings that could not be grown are flagged `below_quantum` rather than
reported.

**4. Battery power changes everything except the results.** Unplugged, this laptop drops
from 1696 MHz to a pinned 1297 MHz, every timing rises, and every quality metric stays
byte-identical. `preflight()` refuses to start on battery, and `ConditionsMonitor`
samples power source and CPU frequency *during* a sweep, because a cable can come out at
run seven of twenty and nothing in the output would show it.

**The frequency channel cannot certify the absence of throttling, and no longer pretends
to.** `psutil.cpu_freq().current` returns a policy-derived constant on this Windows laptop —
exactly 1696.0 MHz across all 1,755 samples of the main sweep, spanning idle and eight
saturated cores. Reading that constancy as "no throttling observed" is precisely the error
this project condemns in codecarbon's utilisation channel, and the project committed it.
`ConditionsMonitor.report()` now returns `throttled=None` rather than `False` when the
channel is unresponsive, alongside `frequency_sensor_responsive=False`. What stays live is
narrower but real: the channel *does* detect a change of power **policy**, because it reads
1297 MHz on battery against 1696 on mains.

Two further guards follow the same principle:

- **Runs are sequential, always.** An `ExclusiveLock` enforces it. Two runs sharing four
  cores charge each other's CPU time to whichever holds the core.
- **A busy machine produces marked output.** Rows measured above a load threshold are
  stamped `trustworthy=False`, and the analysis **refuses to run on them** unless
  explicitly overridden.

---

## What is measured

| stage | amortisation | what it is |
|-------|--------------|------------|
| `train` | once | fitting the model |
| `rerank_setup` | once | item-item similarity the reranker needs |
| `retrieve_score` | per request | scoring the catalogue for a user — the family-specific half |
| `retrieve_select` | per request | taking the top-n from those scores — identical code for every family |
| `rerank` | per request | selecting k items from the candidate set |

`retrieve_score` and `retrieve_select` are split because selection turned out to be the
**majority** of retrieval cost — 99.9 % of it for popularity. Folded into one figure it
would compress the families toward each other and credit them for work none of them does
differently.

### Families

Grouped by the *shape* of their cost, not by accuracy, because a break-even only exists
if the curves cross.

| family | training | serving |
|--------|----------|---------|
| `popularity` | negligible | negligible — one vector, same for everyone |
| `itemknn` | one sparse product | **scales with catalogue size** |
| `als` | **iterative, expensive** | one thin dot product |
| `multvae` | expensive | one forward pass |
| `gru4rec` | **very expensive** | forward pass over the user's replayed history |

All are **work-bounded**: a fixed number of epochs, no early stopping on wall-clock. A
stopping rule that depends on machine speed makes both quality and cost properties of the
hardware, which is how the companion project's tabu solver became non-portable — it got
measurably better on a faster CPU at identical settings.

The LLM family is deliberately skipped, with the slot documented: its energy burns in a
datacentre that cannot be instrumented from here, and reporting an API-derived estimate
beside directly measured CPU-seconds would put two incomparable things in one column.

---

## Running it

```bash
pip install -e ".[dev]"          # core
pip install -e ".[rerank]"       # the D-Wave stack, needed for every reranker
pip install -e ".[energy]"       # codecarbon -- required to reproduce the energy check
pip install torch --index-url https://download.pytorch.org/whl/cpu   # neural families
```

`[energy]` is not optional for reproducing §5. It was omitted from the documented install
for most of this project's history, and `codecarbon` is commented out of
`requirements.txt`, so the instructions above could not reproduce the project's own third
claim. Verified by installing from these lines into an empty environment and running the
experiment, rather than by reading the file.

The companion checkout must be findable — `../qubo-rerank` by default, or set
`GREEN_RERANK_COMPANION`. Datasets are located, never copied: `data/`, then
`$GREEN_RERANK_DATA`, then the companion's `data/`.

```bash
python -m experiments.validity --out results/validity_v2                 # the energy-axis check
python -m experiments.sweep    --config experiments/configs/main_v2.yaml # the measurements
python -m experiments.analyse  --results results/main_v2                 # cost tables, break-even
python -m experiments.compare  --results results/main_v2                 # paired accuracy tests
python -m experiments.figures  --results results/main_v2                 # plots
python -m experiments.verify_claims                                      # 36 assertions on the raw records
```

**Measure cost with the thread count pinned.** Prefix the sweep with
`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`. CPU-seconds counts every
thread, so a stage whose thread count is chosen at runtime by BLAS carries that choice into
its cost — which is what made this project's original headline break-even irreproducible.
The committed sweeps were not run that way, and the report reports the consequence.

`verify_claims` is the check that matters, and it is a *verifier*: 36 assertions, each of
which can fail, computed from `runs.csv`, `readings.csv` and `per_user.csv` only. It never
reads a table written by `analyse.py`, so a stale or hand-edited `tables/` directory cannot
make it pass. `experiments/headline.py` reports the same quantities readably and is
explicitly **not** a verifier — it contains no assertions and cannot fail. Conflating the
two is how a reporting script comes to be trusted as a check.

`validity` runs in about two minutes and needs no dataset: it applies a known graded
load and reports what the energy backend says about it. On a machine with working power
counters it should show a clear response; on the development machine it does not, which
is §5 of the report.

The sweep resumes by default: an interrupted run picks up the cells it has not done.
Repeat is the outermost loop, so an interrupted sweep still leaves one complete
observation of every cell rather than five of the first family and none of the rest.

Every results directory carries a `manifest.json` recording the revision of **both**
repositories, package versions, machine, measured clock quantum, and the preflight record.
It distinguishes `dirty` — the measured *code* differs from its revision, so the numbers
cannot be regenerated — from `tree_dirty`, where only documentation or analysis differs,
which does not affect the measurement. The three superseded results directories carry
`dirty=True`, which is why they could not be repaired and had to be replaced; the three
`_v2` sweeps carry `dirty=False` on both repositories.

---

## Testing

```bash
pytest tests/ -m "not timing"          # 277 of 279 tests, 94 % coverage of green_rerank
ruff check .
python tests/mutations.py              # 41 deliberate bugs; all must be caught
python -m experiments.verify_claims    # 36 assertions about the data
python -m experiments.check_report     # does the report say what the data says?
```

**`check_report` must pass before any commit that touches `docs/report.md`.** It diffs every
data table and thirteen prose figures in the report against freshly recomputed values, and
exits non-zero on any difference. It exists because of one specific failure: §4.5 justified a
threshold with a list of twelve interval widths, six of which were not in the data. The
argument the list supported happened to survive, which is what made it dangerous — the prose
was checked for plausibility, and it was plausible. Nothing recomputed it.

The two checkers ask different questions and neither substitutes for the other:
`verify_claims` asks *is this claim true of the data*; `check_report` asks *does the report
say what the data says*. A number can be hand-typed into prose and be wrong while every
assertion about the data still passes. Tables the checker deliberately skips are listed in
its `NOT_CHECKED` with a reason, and it fails if one of those entries goes stale — a table
that is silently uncovered reads as a table that passed.

Measured, not remembered: 277 selected tests all pass, `coverage` reports **94 %** of
`green_rerank` (76 % including the `experiments/` drivers), and `tests/mutations.py` reports
**41 caught, 0 survived**.

Tests assert invariants rather than chase coverage — the target is anything that could
fail *silently*.

`tests/mutations.py` is the check on the checks. Coverage says a line ran; it does not
say that breaking that line would fail anything, and in a project about defects that
leave output looking normal, that is the distinction that matters. Each entry introduces
a mistake someone could really make — a forgotten division, an inverted comparison, a
guard removed because it looked redundant — runs the tests that ought to object, and
reports whether they did. **Four survived the first run**, and each was this project's
characteristic failure.

Twelve mutations were added after the external audit, one for each defect it found, so that
each specific regression is caught rather than merely fixed — including `balanced_quota`
being dropped from the registry, the stochastic solvers losing their seed, `lam` not
reaching the classical solvers, exposure parity ignoring the catalogue group count,
`runs.csv` recording the requested depth instead of the actual one, the paired comparison
silently keeping one repeat, and a pinned frequency sensor being allowed to certify a clean
run.

The tests that have already earned their place:

- fairness groups are positionally aligned with the matrix columns (mutation testing
  found that reversing them left the whole suite green — every exposure-parity number
  would have measured a permutation of the truth while staying in range and still
  responding to reranking)
- top-k selection matches a reference lexsort element-for-element, including on
  tie-saturated and `-inf`-containing inputs
- a shared measurement session does not leak readings between runs (this one caught a
  live bug: costs would have climbed monotonically through a sweep with every individual
  row still looking plausible)
- the candidate set never exceeds what a user can be shown (this one caught a leakage
  bug: on a 147-item catalogue, asking for 200 candidates returned the user's own
  history as `-inf` padding, which became NaN in the reranker's relevance vector)
- a bootstrap over one repeat is refused rather than reported as a zero-width interval
- results written into the working tree do not count as dirty *code* in the manifest,
  or the provenance flag would be true in every run and mean nothing
- GRU4Rec's embedding reserves index 0 for padding
- held-out items never appear in the training matrix

Run with `--strict-companion` wherever the companion checkout is present, so its absence
fails loudly instead of quietly shrinking the suite.

---

## Licence

MIT.
