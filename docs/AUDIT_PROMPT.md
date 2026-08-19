# Adversarial audit prompt

Give everything below the line to an independent reviewer working in a fresh session at
the repository root, with no prior context on the project.

It is written to be hostile to the work, not helpful to it. An audit that confirms what
the author already believes has told them nothing.

---

You are auditing a research codebase and the empirical claims it makes. Your job is to
**find what is wrong with it**, not to summarise it or praise it. Assume the author is
competent, motivated to believe their own results, and has already convinced themselves.
Your value is entirely in what you catch.

## The project

`green-rerank` measures the *cost* of a recommender pipeline stage by stage — training,
retrieval, reranking — rather than reporting one energy figure per experimental run. It
claims that separating costs paid once from costs paid per request turns a cost table
into a break-even request volume at which one model family stops being the cheaper
choice.

It is the companion to `feasible-rerank`, a separate private repository that should be at
`../qubo-rerank`. **Every accuracy metric in this project is computed by companion code**,
which this project imports rather than reimplements. Claims that depend on that code are
only as good as it is, and you should treat the boundary between the two repositories as
a place where errors hide.

Read in this order: `README.md`, then `docs/report.md`, then the code.

## What is claimed

The report states its findings in a summary section at the top and derives them in §7.
Read them there rather than from this prompt — a claim restated by the person asking for
the audit is a claim already framed favourably.

## How to audit

Work from the data outward, not from the prose inward. Results are on disk in `results/`,
with raw per-stage measurement windows in `readings.csv`, derived per-run figures in
`runs.csv`, and per-user metrics in `per_user.csv`. **Re-derive the headline numbers
yourself from `readings.csv`** rather than checking `runs.csv` against the report; the
derivation is exactly where an error would live and reading only the derived file would
step over it.

**Not every directory under `results/` is live, and auditing a dead one wastes your time.**
`main/`, `depth/`, `rerankers/`, `energy/` and `validity/` are **superseded** -- measured
with defects the project later found, and several record `dirty=True`, meaning the code
that produced them cannot be checked out. `results/README.md` gives the reason per
directory. The report is supposed to cite none of them.

Test that rather than accept it: grep the report for any number traceable to a superseded
directory. A stale citation is an easy and invisible way for a retracted figure to survive,
and it is exactly what the author would miss by rereading.

Live directories: `main_v2/`, `depth_v2/`, `rerankers_v2/`, `validity_v2/`,
`validity_v2_repeat1/`, and three `_pinned` counterparts described below.

There are two author-written checkers, and **neither is evidence on its own**.

`experiments/verify_claims.py` recomputes 36 claims from the raw measurement records
(`runs.csv`, `readings.csv`, `per_user.csv`, `graded_load.csv`).
**Do not treat its passing as evidence.** It was written by the same author as the code it
checks and could test weaker statements than the report makes, or omit the claims that are
hardest to support. An earlier version was substantially tautological -- it read the
tables `analyse.py` wrote and confirmed they said what the report said -- and was rebuilt
to recompute from `readings.csv` / `per_user.csv` instead. Check that the rebuild is real:
any check that still consumes `tables/` is verifying the analysis against itself. Read it critically and ask what it
does *not* check. If you find a claim in the report with no corresponding check, that gap
is itself a finding.

It also has a documented history of pointing at the wrong data: until recently it defaulted
to a superseded validity directory, and was thereby certifying two claims that a clean
re-run had already refuted. Check every default path it uses, not only its arithmetic.

`experiments/check_report.py` diffs every table and thirteen prose figures in
`docs/report.md` against freshly recomputed values, exiting non-zero on any difference. It
exists because §4.5 once justified a threshold with a list of twelve numbers, six of which
were not in the data -- and the argument that list supported happened to be correct, so
nothing looked wrong. Attack it the same way: it exempts some tables in a `NOT_CHECKED`
list, and whether those exemptions are honest is a fair question. A table that is silently
uncovered reads exactly like a table that passed.

Likewise `tests/mutations.py`, which introduces deliberate bugs and asserts the tests
catch them. Ask whether the mutations are the ones that matter or the ones that were easy
to catch.

## Specific things to attack

**The measurement.** The cost unit is CPU-seconds, and the project argues this is
necessary because its energy backend cannot see CPU load. Check whether that argument is
sound and whether the substitution is honest — in particular whether any conclusion is
stated in energy terms that only holds in time terms. There is a claimed clock quantum of
15.625 ms and a repeat-until-measurable scheme built on it; verify the quantum is real on
this machine and that the repetition arithmetic divides correctly.

**The uncertainty.** The break-even is reported as a bootstrap interval. Check the
resampling is done correctly, that the interval means what the report says it means, and
that the rule for declaring a crossover "stable" is not tuned to admit the crossover the
project wanted. Ask what fraction of crossovers are reported versus computed, and whether
the unreported ones are unreported for a principled reason.

**Leakage.** Leave-one-out evaluation, a candidate-retrieval stage, and a reranker are
three places a held-out item can leak back into scoring. The project claims to have found
and fixed one such bug. Look for the others. Pay attention to `exclude_seen` masking, the
candidate cap in `run_pipeline`, and the mapping between catalogue item ids and matrix
column indices.

**The accuracy comparisons.** These are paired per-user tests with a multiple-comparison
correction. Check the pairing is on the same users, that the correction covers the whole
reported family rather than a subset chosen after seeing results, and that
"lower is better" metrics are scored in the right direction.

**The pre-registrations.** Three sweeps -- `main_pinned/`, `depth_pinned/`,
`rerankers_pinned/` -- carry a `prediction` block inside their own `manifest.json`, claiming
to record what would confirm or falsify a hypothesis *before* the run produced an answer.
The report leans on that ordering. **Verify it rather than believe it:** the predictions are
supposed to have been committed to git before the corresponding results directory existed,
so `git log` on each config against the manifest's `created_utc` will show whether the claim
is true. If a prediction was written or edited after the numbers were known, every
conclusion drawn from "we predicted this" collapses -- and that is the most serious finding
available in this repository.

Then ask whether the registered thresholds were placed where they could plausibly fail, or
set wide enough to pass whatever happened.

**The thread-count result.** The project claims CPU-seconds is biased upward on
thread-parallel stages, because OpenMP threads spin-wait and the kernel charges that as
busy, and that pinning the thread count removes both variance and bias. The `_v2` /
`_pinned` pairs are the evidence. Check the pairs differ *only* in thread count, that
accuracy is bit-identical across each pair as claimed -- if it is not, the intervention
touched more than cost -- and that the report's remaining unpinned figures are flagged
wherever they appear.

**False precision.** At least one figure here was quoted to three significant digits when
its denominator was a handful of clock ticks, so the ratio could only move in ~20 % steps.
The author found that one. Look for others: any ratio whose denominator is a cheap stage is
a candidate, and the honest fix is to state the granularity rather than the digits.

**Confounds in the cost comparison.** Every family is measured on the same machine in the
same sweep, but not necessarily under identical conditions. Look for anything that
differs systematically between families other than the family itself — memory pressure,
BLAS thread counts, ordering effects, cache warmth from the preceding run.

**The retractions.** This report retracts several claims from its own earlier version --
including a fairness result and an accuracy-versus-depth relationship -- and deletes a
section whose supporting sweep cannot be regenerated. Check the retractions are real rather
than cosmetic: that the retracted claim does not survive elsewhere in softer language, and
that each replacement claim is actually supported. A report advertising its own corrections
can use them as a credibility device. Test whether these earn it.

**Generalisation.** The study runs on five catalogues and one machine. Identify every
place the report generalises beyond what it measured, and every place it correctly
refuses to. Both lists are informative.

**The statistics.** At least one quantity in this project can be summarised two defensible
ways that give different answers. Find any others, and check the report uses one
consistently.

## What would count as a serious finding

In rough order of severity:

1. A reported number that cannot be re-derived from the raw readings.
2. A claim whose supporting analysis has a bug that changes its direction or magnitude.
3. Leakage of held-out data into any scored quantity.
4. A statistical comparison that does not support the strength of the sentence built on it.
5. A confound that could explain a difference the report attributes to a model family.
6. A guard or check that does not actually fire when its condition is met.
7. Prose that overstates what the data shows, including hedged claims that are hedged in
   the wrong place.

## What is not a finding

Style, naming, formatting, comment density, test count, and coverage percentage. Do not
report these. Do not suggest refactors. Do not propose additional features. The question
is whether the claims are true and the measurements sound, nothing else.

## Running things

There is a virtual environment at `.venv`. The test suite is `pytest tests/ -m "not
timing"`; the `timing` marker covers tests that assert real elapsed behaviour and can be
run separately. Passing `--strict-companion` turns companion-dependent skips into
failures, which is what you want if `../qubo-rerank` is present.

Both checkers run without arguments:

```bash
python -m experiments.verify_claims    # 36 assertions about the data
python -m experiments.check_report     # does the report say what the data says
```

**`../qubo-rerank` is read-only.** It is a finished, published project. Import from it and
read it, but modify no file under it; if you find a bug there, report it rather than fix it.

If you re-run a sweep: the three `_pinned` directories were produced with
`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` set and the `_v2` ones without.
Reproducing either without matching that will not give comparable costs.

**Measurements need an idle machine.** The analysis refuses to read rows measured under
CPU contention. If you re-run any sweep, check nothing else is running first, and expect
the refusal if something is — that refusal is a feature and you should verify it works
rather than route around it.

## How to report

For each finding: what you checked, what you found, the command or file and line that
demonstrates it, and how severe it is. Distinguish clearly between:

- **confirmed defect** — you reproduced it,
- **suspected** — the code looks wrong but you did not demonstrate the consequence,
- **unverifiable** — you could not check it, and why.

If a claim survives your attempt to break it, say so briefly and say what you tried. A
claim that survived a serious attack is worth more than one nobody examined, and the
author needs to know which is which.

End with the single thing you would most want fixed before this is shown to anyone.
