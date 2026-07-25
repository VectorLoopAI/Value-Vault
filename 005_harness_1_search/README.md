# 005 — Harness-1: the search agent that remembers less

Companion assets for the Vector & Loop video **"Search Agent Harness: The 20B Model That
Beats GPT-5.4."**

**Video:** [link placeholder — added after upload]

Source paper: *"Harness-1: Reinforcement Learning For Search Agents With
State-Externalizing Harnesses"* — Pengcheng Jiang, Zhiyi Shi, Kelly Hong, Xueqiang Xu,
Jiashuo Sun, Jimeng Sun, Hammad Bashir, Jiawei Han (UIUC / UC Berkeley / Chroma, 2026).
Paper's own code: https://github.com/pat-jj/harness-1

## What this is

The video's argument: a search agent doesn't need a bigger model, it needs a smaller job.
Split the **policy** (semantic decisions only — what to search, what to keep, what to
verify, when to stop) from a **stateful harness** that owns the recoverable bookkeeping
(candidate pools, a curated set, an evidence graph, verification records). This folder is
a runnable, dependency-light reference implementation of that split — not the paper's
production code, but a faithful reproduction of every mechanism named in the video, wired
to the exact published constants (cap=30, auto-seed k=8, compression K=4, dedup Jaccard
0.85, reward π∅=-0.2/β=2/ν0=6, turn cap 40, LoRA rank 32).

```
value_vault/
├── README.md                                (this file)
├── system_prompts/
│   ├── policy_system_prompt.md               reference reconstruction of the search-policy prompt
│   └── verify_entailment_prompt.md           the strict per-document entailment prompt behind verify()
├── configs/
│   ├── harness_config.yaml                   all harness + reward constants, paper values flagged
│   ├── sft_config.yaml                       stage-1 SFT trainer config (899 trajectories, LoRA r=32)
│   └── rl_config.yaml                        stage-2 RL trainer config (CISPO, SEC-only, 3,453 queries)
└── code/
    ├── working_memory.py                     WORKINGMEMORY state machine: curate, auto-seed,
    │                                          evidence graph, compression, dedup, budget-safe render
    ├── reward.py                             the terminal-only reward function (§2.3 / SEG 17)
    └── demo.py                               end-to-end runnable demo tying the three together
```

## Quickstart

Only external dependency is PyYAML (used to load the config files); everything else is
Python 3.10+ stdlib.

```bash
cd value_vault
pip install pyyaml

python3 code/demo.py
```

`demo.py` runs a toy two-query episode: ingests mock search results (triggering
auto-seed), curates and verifies a document, promotes it to "very high", renders the
budget-safe prompt state, and scores the trajectory with the reward function — printing
the evidence-graph summary and the reward breakdown at the end.

## What's an exact paper value vs. an illustrative default

`configs/harness_config.yaml` marks every constant `(paper)` or `(illustrative default)`.
The structural mechanisms and every hyperparameter named in the video are wired in exactly
as published: cap=30, auto-seed k=8/tag=fair, compression K=4, dedup Jaccard=0.85,
π∅=-0.2, β=2, ν0=6, turn cap=40, LoRA rank 32/3 epochs/899 trajectories/step-550 init,
CISPO/no-KL-anchor/SEC-only/3,453 queries. The paper does **not** publish the individual
scalar weights that combine the reward's sub-terms (set-quality weight, coverage weight,
etc.) — those are marked `(illustrative default)` in the config and in `code/reward.py`,
so the reference code runs; tune them for your own setup.

## The one-line geometry to remember

> The policy decides. The harness remembers. Move the ledger out of the weights and into
> a deterministic, inspectable environment layer — that's capability your model no longer
> spends gradient, or context, relearning every step.
