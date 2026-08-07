# 006/007 — SkillOpt: a training loop for an agent's SKILL.md

Companion assets for the Vector & Loop two-part episode **"Agent Skills Get a
Learning Rate, Not a Rewrite (Part 1)"** / **"Agent Skills That Beat Their
Own Training Harness (Part 2)."** This one folder is shared by both parts —
see `videos/007_skillopt_p2/value_vault/README.md` for the pointer used
there.

**Part 1 video:** (https://www.youtube.com/watch?v=-wA36Nnz0d4)
**Part 2 video:** (https://www.youtube.com/watch?v=78cDurifNGM)

Source paper: *"SkillOpt: Executive Strategy for Self-Evolving Agent
Skills"* — Yifan Yang, Ziyang Gong, Weiquan Huang, Qihao Yang, Ziwei Zhou,
Zisu Huang, Yan Li, Xuemei Gao, Qi Dai, Bei Liu, Kai Qiu, Yuqing Yang,
Dongdong Chen, Xue Yang, Chong Luo (Microsoft / Shanghai Jiao Tong
University / Tongji University / Fudan University, 2026).

## What this is

The episode's argument: an agent's skill file doesn't have to be hand-written
once and frozen — it can be **trained**, with the actual discipline of a
deep-learning optimizer applied to text instead of weights: rollout batches
as the forward pass, minibatch reflection as the backward pass, a **textual
learning rate** capping how many edits land per step, a **held-out
validation gate** that only accepts an edit when it strictly beats the
current score, and an epoch-wise slow update acting as momentum. This folder
is a runnable, dependency-free reference implementation of that loop — not
the paper's production code, but a faithful reproduction of every mechanism
named in the video, wired to the paper's own default hyperparameters.

```
value_vault/
├── README.md                          (this file)
├── configs/
│   └── skillopt_config.yaml           every default hyperparameter, paper values flagged
├── prompts/
│   ├── analyst_error.md               failure-minibatch → corrective-edit contract
│   ├── analyst_success.md             success-minibatch → preservation-edit contract
│   ├── merge_final.md                 hierarchical merge, failure priority, support_count
│   ├── ranking.md                     utility-ranking + top-L_t clipping contract
│   ├── slow_update.md                 epoch-wise momentum term, protected SLOW_UPDATE block
│   └── meta_skill.md                  optimizer-only memory that never ships
└── code/
    ├── skill_patch.py                 SkillDocument + bounded patch ops (append/insert_after/replace/delete)
    ├── learning_rate_schedule.py      the textual learning rate L_t (constant/linear/cosine)
    ├── gate.py                        the validation gate + rejected-edit buffer
    └── demo.py                        end-to-end toy loop tying all three together
```

## Quickstart

Zero external dependencies — Python 3.10+ stdlib only.

```bash
cd value_vault/code
python3 demo.py
```

`demo.py` runs a two-epoch toy loop over a spreadsheet-style skill: proposes
a small edit pool, ranks it, clips it to that epoch's textual learning rate,
applies it as a bounded patch, and runs it past the validation gate — one
epoch is accepted (the selection score improves), one is rejected (the score
doesn't move), printing an `edit_apply_report`-style JSON log plus the
epoch-local rejected-edit buffer, exactly as described in §3.5.

## What's an exact paper value vs. an illustrative default

`configs/skillopt_config.yaml` marks every constant `(paper)` or
`(illustrative)`. The training loop's structure and every hyperparameter
named in the video are wired in exactly as published: 4 epochs, rollout
batch 40, reflection minibatch 8 with 16 analyst workers, `L_t` = 4 with
cosine decay to a floor of 2, strict-accept validation gating, slow-update
sampling of 20 tasks/epoch, patch mode as the default edit mode. The paper
does **not** publish the numeric weights `Ranking.md` uses to combine its
four criteria (systematic impact, complementarity, generality,
actionability) — `prompts/ranking.md` flags this, and `demo.py`'s
`rank_by_utility()` uses a simple stand-in (`support_count`, then
`utility`) so the reference code runs; replace it with your own ranking
model for a real deployment.

## The one-line geometry to remember

> A frozen model, plus an external text file that's versioned, edited under
> a budget, and validated against a held-out split, behaves like a trained
> model. The gate is the whole difference — it's what turns self-editing
> into optimization.
