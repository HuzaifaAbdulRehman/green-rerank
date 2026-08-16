# The cost of a recommendation, by stage

**Status:** methodology and the energy-validity result are complete. The cross-catalogue
sweep has not yet been run on a quiet machine, so the break-even and frontier sections
are marked as pending rather than filled with numbers taken under contention. Every
section below that states a figure states where it came from.

---

## 1. The question

A deployer choosing a recommender model wants to know what it will cost to run. The
green-recommender literature answers a different question: it reports the energy of an
experimental *run*, which adds together

- a cost paid **once**, at deployment — training; and
- a cost paid on **every request** — retrieval, ranking, reranking.

Those are not the same kind of quantity and their sum is not interpretable. A model that
trains for an hour and then serves nearly free, and one that trains instantly and then
burns an hour answering queries, can report identical totals and imply opposite
decisions. The sum is dominated by whichever term the experimenter's setup happened to
emphasise: run the evaluation over 100 users and training dominates; run it over
10 million and serving does. Neither number is a property of the model.

Separating them gives

```
C(N) = C_once + N · C_per_request
```

Two families are then two lines, and lines with different slopes **cross**. The crossing
point — the request volume at which the cheaper choice changes — is the form a
deployment decision actually takes, and it is what this project reports.

## 2. What is not claimed

The obvious claim, "nobody has compared model families on energy", is false and this
project does not make it. Wegmeth, Beel and colleagues (ACM TORS 2025; code at
`ISG-Siegen/recsys-carbon-footprint`) measured 63 algorithms across 14 datasets with a
physical smart-plug meter, and separated fit / predict / evaluate. That work is more
comprehensive on the axis it covers than anything here.

Three things it does not do, which this project does:

1. **Amortisation.** Prior work reports energy per run. The break-even request volume
   does not appear.
2. **The reranker as a line item.** The stage decomposition stops at predict. Fairness
   rerankers are proposed steadily in the fairness-in-ranking literature and, as far as
   this search found, have never been costed.
3. **Validity of the measurement instrument** on hardware without power counters —
   which is most laptops, all of Windows, and every VM.

## 3. Setting: why a 15 W laptop is the right machine

Intel i5-8350U (4 cores / 8 threads, 15 W TDP), integrated graphics, 32 GB RAM,
Windows 10. No discrete GPU, no RAPL, no smart plug, no cloud budget.

This is a constraint, and it is also the regime the literature does not cover. Published
energy studies run on server or workstation hardware with instrumentation attached. A
small vendor deploying a recommender does not have that machine; they have this one.
Results measured here describe the hardware such a deployment actually runs on.

The measurement consequences are handled explicitly rather than absorbed: see §4.

## 4. Measurement method

### 4.1 The unit is CPU-seconds

Not kWh, and the reason is §5.

CPU-seconds are read from `time.process_time()`, which the kernel maintains and which
counts **every thread**. That matters more than it sounds: a BLAS matmul spread over four
cores registers four CPU-seconds per wall-second, and a torch training step likewise.
Wall-clock would report such a stage as four times cheaper than it is, which is exactly
backwards for an energy proxy. Measured here, GRU4Rec's training consumed 270.9
CPU-seconds against 69.8 seconds of wall-clock — a 3.9× parallelism that wall-clock
would have hidden entirely.

Joules are reported only through `Reading.joules(watts_per_cpu_second)`, which has **no
default argument**. A joule figure cannot appear anywhere in this project's output
without its conversion assumption visible beside it.

This does not weaken the break-even result. `C(N)` is linear, so a crossover computed in
CPU-seconds is the *same request count* as one computed in joules, provided the
conversion is a constant.

### 4.2 Stages

| stage | amortisation | contents |
|-------|--------------|----------|
| `train` | once | fitting the model |
| `rerank_setup` | once | item–item similarity the reranker requires |
| `retrieve_score` | per request | scoring the catalogue for a user |
| `retrieve_select` | per request | taking the top-n from those scores |
| `rerank` | per request | selecting k from the candidate set |

Retrieval is split into scoring and selection because selection turned out to be the
**majority** of retrieval cost — 99.9 % of it for popularity, ~50 % for ItemKNN. Reported
as one figure it would compress the families toward each other and attribute most of
their serving cost to code that is identical across all of them. Splitting it isolates
the part that is genuinely the family's own.

There is deliberately **no scoring stage**. Metric computation is O(k²) per user in pure
Python; inside a measured window it would be noise against a training run and the
majority of the reading against a cheap retrieval — error concentrated exactly where the
comparison between families is decided. `Stage` has no member for it, so no call site can
pass one.

### 4.3 The four traps

Each was found the hard way. They share a signature: **the run completes, the table looks
normal, and only the cost column is wrong.**

**The probe is not free.** `EmissionsTracker.start()` interrogates the hardware for
seconds. Timing from before it charged that constant to whatever followed; in the
companion project a baseline doing 0.008 s of real work read 5.4 s. The clock now starts
strictly after the probe and stops strictly before teardown.

**The clock is 15.625 ms, not 100 ns.** `time.get_clock_info("process_time")` advertises
100 ns resolution. The true quantum is the scheduler tick — five orders of magnitude
coarser. A 3 ms stage reads either `0.0` or `0.0156`, and two stages differing tenfold
can report the same number. `measure_repeated` repeats work until the window spans ~20
quanta, bounding quantisation error at ~5 %, and divides. Readings that could not be
grown are flagged `below_quantum` rather than reported as measurements. In practice this
means repeat counts from 1 to 2,434 across stages in a single run, all normalised to a
0.3125 s window.

**Battery changes everything except the results.** Unplugged, this machine drops from
~3.6 GHz to a pinned 1.297 GHz; every timing rises ~2.8× and every quality metric stays
byte-identical. Preflight refuses to start on battery. Because a cable can come out at
run seven of twenty, `ConditionsMonitor` also samples power source and CPU frequency
*during* a sweep and flags the whole run if either moves.

**Contention is charged to whoever is running.** Runs are strictly sequential, enforced
by an atomic lockfile. Before starting, machine load is sampled; above a threshold the
sweep aborts, and above a lower threshold every row is stamped `trustworthy=False` and
**the analysis refuses to read it**. This is not hypothetical — during this project's
development the machine was frequently occupied by the companion project's own
experiments, and the guard is what kept those hours from producing a plausible-looking
results table.

### 4.4 Uncertainty on the break-even

A crossover is a ratio of two differences:

```
N = (C_once,B − C_once,A) / (C_per_request,A − C_per_request,B)
```

so it amplifies the noise in both. Repeated measurements of *identical* work on this
machine differ by tens of percent — popularity's training stage needed 1,774 repeats in
one run and 2,434 in the next to fill the same window. When two families' per-request
costs are within that spread, the denominator can approach zero and the crossover can
move by orders of magnitude or cease to exist.

Every configuration is therefore measured with repeats, and the crossover is reported as
a **percentile bootstrap interval** over them, resampling each family's `(once,
per_request)` pairs jointly — jointly because a moment of background load inflates both,
and resampling them independently would manufacture combinations never observed and
report an interval narrower than the truth.

Replicates in which the lines do not cross are **counted, not discarded**. Their share is
reported, and a crossover found in only a minority of replicates is a null result, not a
wide interval. This is not a theoretical safeguard: on cost figures of the size measured
in this project's early synthetic runs, only **7 %** of replicates crossed, and among
those the interval spanned 1,303 to 710,392 requests. A single-observation estimate had
reported `N = 13,736`. That number was false precision, and the earlier draft of this
project stated it.

## 5. Result: the energy backend is blind here

**This is a measured result, not a caveat.**

`codecarbon` on hardware without RAPL estimates CPU power from rated TDP and a
utilisation sample. If that estimate does not track utilisation, reported energy
degenerates to `kWh ≈ constant × seconds`, and every "energy" conclusion drawn from it is
a wall-clock conclusion in different units.

Tested directly with a graded load — 0, 1, 2, 4 and 8 busy **processes** (processes, not
threads: the GIL would let a thread-based load saturate one core while the rest idled,
handing the backend an easier test than it needs to pass).

Findings, on the original observation (codecarbon 2.x):

| load | reported CPU power | reported utilisation |
|------|--------------------|----------------------|
| idle | 1.501 W | 0.0 % |
| 8 threads saturated | 1.815 W | 0.0 % |

A 1.21× swing against a true dynamic range of roughly 10× for this part; utilisation
pinned at zero throughout; the fully loaded window reporting **less** total energy than
idle (7.290e-05 vs 7.371e-05 kWh); and RAM billed at a hardcoded constant 10.000 W that
dominates the total.

Re-run on **codecarbon 3.3.0** during this work, one of those findings has changed and is
reported as measured rather than restated: `cpu_util_pct` is no longer always zero — it
reported 16.7 % under a 4-worker load in one window. `ram_watts` remains **exactly**
10.000 W across the entire span from idle to saturation. A channel that is bit-for-bit
identical from idle to full saturation is not a noisy measurement of the load; it is not
a measurement of the load, and it needs no threshold to interpret.

The machine exposes no RAPL. WSL2 does not help — verified rather than assumed:
`/sys/class/powercap` exists but is empty and `/dev/cpu/0/msr` is absent, because the
hypervisor does not pass the counters through. Colab is not a substitute either, since a
shared CPU reintroduces contention.

**Consequence.** CPU-seconds is the reported unit. The `codecarbon` failure is folded in
as a result of the project rather than worked around silently, and
`experiments/validity.py` reproduces it on any machine in about two minutes.

## 6. Datasets

Six registered catalogues, spanning roughly two orders of magnitude in size, because the
break-even claim is a statement about how serving cost scales with catalogue size and
cannot be demonstrated on one.

| catalogue | users | items | interactions | groups |
|-----------|-------|-------|--------------|--------|
| `gift_cards` | 456 | 147 | 2,498 | popularity tiers |
| `software` | 1,779 | 727 | 10,073 | popularity tiers |
| `ml100k` | 943 | 1,349 | 98,344 | curator genres |
| `luxury_beauty` | 3,589 | 1,365 | 23,860 | popularity tiers |
| `digital_music` | 16,252 | 11,268 | 127,939 | popularity tiers |
| `appliances` | 13 | 4 | 23 | **excluded** |

All after 5-core filtering and a leave-one-out split, using the companion project's
preprocessing so that the two projects agree exactly on which interactions survive.

`appliances` is excluded and the exclusion is stated rather than left as a gap: the
ratings-only export is so long-tailed that 5-core filtering reduces it to 13 users and 4
items. That is a property of the export, not a loading bug, and a full row of metrics
computed over four items would be a number rather than a measurement. The driver refuses
it by a viability check on every catalogue.

MovieLens uses **curator genres** for fairness groups rather than popularity tiers. A
popularity partition is derived from the same interaction counts being evaluated, so any
fairness result on it can be argued to be structural; genres are assigned independently
of the data.

## 7. Results

### 7.1 Break-even between families — *pending*

Requires the cross-catalogue sweep on an unloaded machine.

### 7.2 The cost of fairness reranking — *preliminary*

From a driver-validation run on `gift_cards` (marked untrustworthy — the machine was
occupied — and reported here only as an order of magnitude):

| family | rerank share of serving cost | serving-cost multiplier |
|--------|------------------------------|-------------------------|
| `popularity` | 92.8 % | 13.9× |
| `itemknn` | 90.9 % | 10.9× |
| `als` | 92.0 % | 12.5× |

The shape is consistent across families: the fairness reranker is roughly an order of
magnitude more expensive than the entire retrieval it sits on top of, and it dominates
per-request cost. If this survives measurement on a quiet machine it is the project's
most directly actionable number, because it is a cost nobody currently reports at all.

Accuracy moved in **both** directions across catalogues in preliminary runs — reranking
lowered NDCG on `gift_cards` (0.227 → 0.159) and raised it on `digital_music`
(0.048 → 0.062). Both directions will be reported.

### 7.3 Efficiency frontier — *pending*

### 7.4 Retraining cadence — *pending*

The plain line assumes a model is trained once and serves forever, which no deployment
does. Under periodic retraining the once-cost recurs and a family with expensive training
loses its amortisation advantage in proportion to how often it is retrained — enough to
reverse the verdict.

## 8. Threats to validity

**One machine.** Every figure is from a single laptop. The break-even *request counts*
should transfer better than the absolute costs, since both sides scale together, but this
is an argument rather than a measurement.

**Python implementations.** ItemKNN and ALS are written against numpy rather than taken
from a compiled library. This keeps the training cost measurable rather than a black box,
and both are dense linear algebra where numpy dispatches to BLAS — but a compiled
implementation would shift the absolute numbers.

**Leave-one-out with a single held-out item** makes NDCG@10 small in absolute terms and
noisy per user. It is the companion project's protocol, kept deliberately so the two are
comparable.

**The reranker's problem size is fixed** at 200 candidates. Its cost scales with that,
so the reranking share in §7.2 is a statement about a 200-candidate reranker, not about
reranking in general.

**No LLM family.** Deliberately omitted with the slot documented: its energy burns in a
datacentre that cannot be instrumented from here, and an API-derived estimate placed
beside directly measured CPU-seconds would put two incomparable quantities in one column.

## 9. Reproducing

```bash
python -m experiments.validity                              # §5, ~2 minutes
python -m experiments.sweep    --config experiments/configs/main.yaml
python -m experiments.analyse  --results results/main
python -m experiments.figures  --results results/main
```

Each results directory carries a `manifest.json` recording the revision of **both**
repositories — every accuracy metric here is computed by companion code, so a provenance
record naming only this one would be half a record. A dirty working tree is recorded as
`abc1234-dirty`, because that is not a version anyone can return to.
