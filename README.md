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
two reranking conditions, five repeats each. Zero failures, every row passing the trust
check on an idle mains-powered machine, no stage falling below the clock quantum.
Full write-up in [`docs/report.md`](docs/report.md).

**A break-even exists and is measurable.** ItemKNN against ALS on MovieLens 100K crosses
at **N = 112,730 requests** (95 % CI 51,128 – 180,720; 95 % of bootstrap replicates
cross). Below that the neighbourhood model is the cheaper deployment, above it the factor
model. Only 13 of 45 configuration pairs cross stably enough to report — that denominator
is part of the result.

**Fairness reranking is 80–98 % of per-request cost**, multiplying serving cost 4.9× to
43.8×. A deployer adding exposure fairness to a popularity baseline is not paying a
margin, they are paying **24 times** their serving cost. As far as the literature search
found, this is the first published figure for what a fairness reranker costs as a share
of a pipeline.

**Retrieve shallowly when reranking.** Going from 50 to 800 candidates costs 35× more in
the rerank stage (cost scales O(n^1.2–1.3)), delivers **no** measurable fairness
improvement (exposure parity flat at 0.254), and *loses* accuracy.

**Most models do not beat recommending the most popular items.** On MovieLens 100K only
GRU4Rec beats a popularity baseline under a paired per-user test, and only on recall
(37 wins / 11 losses, p = 0.0073) — for 451 CPU-seconds of training against popularity's
0.000167, a factor of 2.7 million. ItemKNN, ALS and MultVAE show no detectable
difference. ItemKNN and MultVAE are *dominated*: costlier than popularity and less
accurate, so they should not be deployed on that catalogue at all. On `software` the
verdict flips and ItemKNN and ALS win clearly — the catalogue-dependence is itself the
finding.

**Retraining cadence is a bigger lever than model choice.** Holding traffic fixed,
GRU4Rec's total cost moves 791× between never retraining and retraining every 100
requests, with accuracy unchanged.

---

## The cost unit is CPU-seconds, and that is a finding

`codecarbon` **cannot see CPU load on the development machine**. Measured on codecarbon
3.3.0 with a graded load — 0, 1, 2, 4 and 8 busy processes, 20 s each, idle machine.
Reproduce with `python -m experiments.validity`:

| busy workers | reported CPU power | reported utilisation | reported RAM power | total energy |
|--------------|--------------------|----------------------|--------------------|--------------|
| 0 | 1.500 W | 0.0 % | 10.000 W | 7.459e-05 kWh |
| 4 | 1.523 W | 0.0 % | 10.000 W | 6.722e-05 kWh |
| 8 | 1.687 W | 0.0 % | 10.000 W | 7.418e-05 kWh |

Utilisation reads exactly zero at every level including eight saturated cores. CPU power
moves **1.12×** across the full span, against a true dynamic range of roughly 10× for
this part. RAM power is exactly 10.000 W throughout — a hardcoded constant, and it
dominates the total. The fully loaded run reports **less** total energy than idle.

A second test regressed reported energy on elapsed time over 144 readings from real
workloads, expecting to find that the energy column was simply a rescaled clock. It is
not, and the truth is worse: R² = 0.55, with the implied kWh-per-CPU-second conversion
varying **13.7×**. Not even a constant misestimate that could be calibrated away.

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
from ~3.6 GHz to a pinned 1.297 GHz, every timing rises ~2.8×, and every quality metric
stays byte-identical. `preflight()` refuses to start on battery, and `ConditionsMonitor`
samples power source and CPU frequency *during* a sweep, because a cable can come out at
run seven of twenty and nothing in the output would show it.

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
pip install torch --index-url https://download.pytorch.org/whl/cpu   # neural families
```

The companion checkout must be findable — `../qubo-rerank` by default, or set
`GREEN_RERANK_COMPANION`. Datasets are located, never copied: `data/`, then
`$GREEN_RERANK_DATA`, then the companion's `data/`.

```bash
python -m experiments.validity                                        # the energy-axis check
python -m experiments.sweep    --config experiments/configs/main.yaml # the measurements
python -m experiments.analyse  --results results/main                 # cost tables, break-even
python -m experiments.compare  --results results/main                 # paired accuracy tests
python -m experiments.figures  --results results/main                 # plots
```

`validity` runs in about two minutes and needs no dataset: it applies a known graded
load and reports what the energy backend says about it. On a machine with working power
counters it should show a clear response; on the development machine it does not, which
is §5 of the report.

The sweep resumes by default: an interrupted run picks up the cells it has not done.
Repeat is the outermost loop, so an interrupted sweep still leaves one complete
observation of every cell rather than five of the first family and none of the rest.

Every results directory carries a `manifest.json` recording the revision of **both**
repositories, package versions, machine, measured clock quantum, and the preflight
record. A dirty working tree is recorded as `abc1234-dirty`, because that is not a
version anyone can return to and it should not look like one.

---

## Testing

```bash
pytest tests/ -m "not timing"
ruff check .
```

Tests assert invariants rather than chase coverage — the target is anything that could
fail *silently*. The ones that have already earned their place:

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
