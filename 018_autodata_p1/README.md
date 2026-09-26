# 018/019 — Autodata: a synthetic data agent that acts like a data scientist

Companion assets for the Vector & Loop two-part episode **"Synthetic Data
Agent: A 4B Model Beats a 397B (Part 1)"** / **"Synthetic Data Agent
Optimizes Itself: 79.6% (Part 2)."** This one folder is shared by both parts
— see `videos/019_autodata_p2/value_vault/README.md` for the pointer used
there.

**Part 1 video:** https://www.youtube.com/watch?v=beF1kH6BiNw
**Part 2 video:** 

Source paper: *"Autodata: An Agentic Data Scientist To Create High Quality
Synthetic Data"* — Ilia Kulikov, Chenxi Whitehouse, Tianhao Wu, Yixin Nie,
Swarnadeep Saha, Eryk Helenowski, Weizhe Yuan, Olga Golovneva, Jack
Lanchantin, Yoram Bachrach, Jakob Foerster, Xian Li, Han Fang, Sainbayar
Sukhbaatar, Jason Weston (FAIR at Meta, 2026).

## What this is

The episode's argument, in two halves. Part 1: don't treat synthetic-data
generation as a fixed prompting recipe — wrap it in a **weak-vs-strong
acceptance loop** (challenger → weak solver → strong solver → judge) that
only keeps an example when the weak solver struggles and the strong solver
succeeds, and let the judge's own report steer the next attempt. The same
loop self-corrects in *either* direction: it makes CS questions harder and
legal questions easier/less degenerate, and wins the downstream RL
comparison both times. Part 2: turn that identical accept/reject shape
**one level up** — mutate the data scientist's own prompts, and keep a
mutant harness only if it strictly beats its parent on held-out validation.
This folder is a runnable, dependency-free reference implementation of both
loops.

```
value_vault/
├── README.md                            (this file)
├── configs/
│   ├── acceptance_criteria.yaml         per-domain thresholds (CS / Legal / Science)
│   └── meta_optimizer_config.yaml       Boltzmann T, iteration budget, the 4 meta-opt conditions
├── prompts/
│   ├── challenger_cs.md                 CS domain: context + question + reference + rubric contract
│   ├── quality_verifier_cs.md           CS domain: context-leakage / rubric screen before solvers
│   ├── extractor_legal.md               Legal domain: raw document -> topic/facts/holdings
│   ├── question_writer_legal.md         Legal domain: client-voiced scenario + rubric
│   ├── loop_judge_legal.md              Legal domain: no fixed thresholds, GRPO-suitability verdict
│   ├── failure_analyst.md               Meta-opt: trajectories -> root-cause failure report
│   └── code_editor.md                   Meta-opt: failure report -> concrete prompt diff
└── code/
    ├── acceptance_gate.py               weak-vs-strong acceptance rule (verifiable + rubric-graded)
    ├── boltzmann_sampler.py             parent selection, P proportional to exp(score / T)
    └── demo.py                          end-to-end toy loop tying all three together
```

## Quickstart

Zero external dependencies — Python 3.10+ stdlib only.

```bash
cd value_vault/code
python3 demo.py
```

`demo.py` runs two toy loops back to back: (1) an inner Agentic
Self-Instruct round — a challenger example scored by a mock weak/strong
solver pair, accepted or rejected by the domain's acceptance rule; and (2)
a meta-optimizer round — two candidate harness prompts scored on a mock
validation set, with the mutant kept only if it strictly beats the parent,
selected next round via Boltzmann sampling over the population's scores.
Both print the same `accepted: bool` decision shape, on purpose — the point
of Part 2 is that it's the *same* gate, one level up.

## What's an exact paper value vs. an illustrative default

`configs/acceptance_criteria.yaml` and `configs/meta_optimizer_config.yaml`
mark every constant `(paper)` or `(illustrative)`. The published thresholds
are wired in exactly: CS domain strong solver ≥0.65 / weak solver <0.5 /
gap ≥20pp; the science domain's pass/fail gate (weak ≤1/4 of 4 attempts,
strong ≥3/4); the meta-optimizer's four-condition win definition (weak
≤65%, weak best-attempt ≤75%, strong 60–95%, gap ≥20pp); Boltzmann
temperature T=0.1; 50 training / 25 validation papers; 233 iterations under
a 6-hour session timeout. The legal domain deliberately has **no** numeric
thresholds in `acceptance_criteria.yaml` — per the paper, the loop-judge
there asks a qualitative "is this GRPO-suitable?" question instead, which
`loop_judge_legal.md` documents; `acceptance_gate.py`'s
`legal_acceptance()` is left as a judge-verdict pass-through rather than a
numeric comparison, faithful to that design choice.

## The one-line geometry to remember

> The gap between a weak solver and a strong solver *is* the training
> signal — keep the example only when that gap exists. Part 2 does the
> exact same thing to the agent that makes the examples: keep the mutant
> harness only when it strictly beats its parent. Weak versus strong, one
> level up.
