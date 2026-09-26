# 016/017 — Compiling agentic workflows into LLM weights (Series A finale)

Companion assets for the Vector & Loop two-part episode **"Agentic
Workflow, No Orchestrator: 3B Beats Itself (Part 1)"** / **"Agentic
Workflow at 55 Nodes: 462x Cheaper (Part 2)."** This is the Series A
finale. One folder is shared by both parts — see
`videos/017_compiling_weights_p2/value_vault/README.md` for the pointer
used there.

**Part 1 video:** https://www.youtube.com/watch?v=ADirjzsva4E
**Part 2 video:** https://www.youtube.com/watch?v=8BecqKFZJgc

Source paper: *"Compiling Agentic Workflows into LLM Weights: Near-Frontier
Quality at Two Orders of Magnitude Less Cost"* — Simon Dennis, Rivaan Patil,
Kevin Shabahang, Hao Guo (i14, University of Melbourne, 2026).

## What this is

The episode's argument: an agentic workflow doesn't have to live in an
orchestrator sitting between the user and the model. This paper compiles
the procedure directly into a small model's weights — a "subterranean
agent" — and proves the win is architectural, not just a capacity trick,
with a same-model control (identical 3B base model, with and without
orchestration). This folder is a runnable, dependency-free reference
implementation of the paper's own formulas, its procedure-graph formalism,
and every data table named across both videos, so you can recompute the
headline claims yourself rather than take the video's word for them.

```
value_vault/
├── README.md                              (this file)
├── configs/
│   ├── compile_pipeline.yaml              the graph formalism + 4-step compile pipeline + training runs
│   └── domains.yaml                       travel / Zoom / insurance domain specs + case-study transcripts
└── code/
    ├── metrics.py                         pct-of-in-context, cost, breakeven, savings-multiplier formulas
    ├── data_tables.py                     every published number from both episodes, source-tagged
    ├── procedure_graph.py                 runnable F=(N,E,n0,T) formalism + acyclic-path enumeration
    └── demo.py                            recomputes every headline claim from the two videos
```

## Quickstart

Zero external dependencies — Python 3.10+ stdlib only.

```bash
cd value_vault/code
python3 demo.py
```

`demo.py` walks through, in order: (1) the adoption-gap ratio that opens
Part 1 (290,000+ orchestration stars vs. ~3,000 compilation stars); (2) the
Part 1 causal core — the same-model control, counting how many of the five
quality criteria compilation wins at p<.001; (3) percent-of-in-context
quality at 3B (travel) and 8B (insurance), recomputed directly from the raw
score tables and checked against the paper's own quoted 82–102% (3B) and
92–98% (8B insurance) ranges; (4) the failure-rate comparison per domain
(5.5% vs. 24.0% on travel); (5) the compound cost-per-conversation ratios,
recomputed and flagged against the paper's own stated multiples where
rounding in the source table creates a small gap, plus the per-token
self-hosting cost reproduction (~65x cheaper, derived from the paper's own
hourly-cost and throughput numbers, not just copied) and break-even
conversation counts; (6) the recompile timeline; (7) the two honesty notes
from Part 2 — the ~87% information-accuracy plateau and the judge-dependent
quality range (83–99% GPT-4.1 vs. 82–102% Claude) — printed explicitly, not
smoothed away; (8) `procedure_graph.py`'s illustrative example, demonstrating
the paper's own `F = (N, E, n0, T)` formalism and acyclic-path enumeration
on a small toy graph (explicitly **not** a reconstruction of any of the
paper's real flowcharts, which aren't published node-by-node — see that
module's docstring).

## What's an exact paper value vs. a partial reconstruction

Every number in `code/data_tables.py` is tagged `(paper, verified)` — copied
from a table or a value directly quoted in
`backlog/011_compiling_workflows_into_weights.md` (itself cross-checked
against the paper's own tables) — or `(paper, computed)` for values
`demo.py` derives from other verified numbers (e.g. percent-of-in-context,
savings ratios). Three known internal rounding/provenance quirks are called
out explicitly rather than silently corrected:

- **Zoom training-conversation count.** The backlog note states "870
  convos/run" across "8 seeds (42–49)," which arithmetically is 6,960, but
  also states the concatenated total is "6,264 training conversations."
  Both numbers are quoted directly from the source; the gap between them is
  not resolved here — `code/data_tables.py`'s `ZOOM_TRAINING_CONVO_DISCREPANCY`
  records both as stated and `demo.py` does not attempt to reconcile them.
- **Compound cost ratios.** Table 6's per-conversation costs are rounded to
  4 decimal places (e.g. Zoom subterranean = $0.0003), so recomputing
  `in_context / subterranean` from those rounded cells doesn't exactly
  reproduce the paper's own stated multiples (128x / 296x / 462x) —
  `demo.py` prints both the recomputed and the quoted multiple and flags
  the delta instead of hiding it.
- **Same-model control deltas.** The paper states deltas (e.g. task success
  Δ=+0.18) that don't always match subtracting the individual rounded table
  cells exactly (4.11−3.93=0.18 checks out, but 4.12−3.96=0.16 vs. the
  stated Δ=+0.17 for naturalness). `data_tables.py` records the paper's
  stated deltas verbatim rather than recomputing from rounded cells.

Nothing in this folder is invented or interpolated — cells not sourced from
the script or backlog note are simply absent, not guessed. Appendix C's
Table 10 (damaged OCR per the backlog note) is deliberately **not**
reproduced at the per-cell level anywhere in this folder — only the paper's
own quoted aggregate ranges (83–99% GPT-4.1 vs. 82–102% Claude) appear.

## The one-line geometry to remember

> A harness is a specification. Once you trust the specification — once you
> know the flowchart your agent should follow — it stops being infrastructure
> you run and becomes training data you compile. The orchestrator was never
> the product. Persistent structure belongs in the weights; transient state
> belongs in the prompt.
