# 010/011 — Effective Feedback Compute: a scoring layer for agent harnesses

Companion assets for the Vector & Loop two-part episode **"Agent Scaling
Laws: Token Count Predicts Nothing (Part 1)"** / **"Agent Scaling Laws: 60%
Cheaper Agents, Real Traces (Part 2)."** This one folder is shared by both
parts — see `videos/011_agent_scaling_laws_p2/value_vault/README.md` for the
pointer used there.

**Part 1 video:** https://www.youtube.com/watch?v=yugJQaT57Uc
**Part 2 video:** https://www.youtube.com/watch?v=OAvCZqOs6Oo

Source paper: *"Scaling Laws for Agent Harnesses via Effective Feedback
Compute"* — Xuanliang Zhang, Dingzirui Wang, Keyan Xu, Qingfu Zhu, Wanxiang
Che (Harbin Institute of Technology, 2026).

## What this is

The episode's argument: your agent's tokens, tool calls, and dollar cost
don't predict whether it succeeds — the feedback it actually receives does,
if that feedback is informative, valid, non-redundant, and retained. This
folder is a runnable, dependency-free reference implementation of the
scoring system built across both episodes: the four-gate event score
(Part 1), its no-oracle estimator and redundancy-aware variant (Part 2),
the task-demand and harness-efficiency decomposition (Part 2), and the
ROI-scored control layer, EFC-ADAPTER, that reads the ledger in real time
(Part 2).

```
value_vault/
├── README.md                    (this file)
├── configs/
│   └── efc_config.yaml          every fixed constant, paper values flagged
└── code/
    ├── efc_score.py             the four gates: EFC_t = kappa * I * V * R * M (Part 1)
    ├── raw_cost.py               C_raw(tau) — the raw-expenditure baseline EFC is measured against
    ├── task_demand.py            D_task — how much feedback a task actually needs
    ├── estimated_efc.py          Estimated-EFC — nine trace-observable features, no oracle (Part 2)
    ├── nrs_efc.py                 NRS-EFC — status/progress/loop gates + ambiguity penalty (Part 2)
    ├── efficiency.py              eta (harness efficiency) vs EFC/D_task — the diagnostic split (Part 2)
    ├── ledger.py                  the per-event ledger: event, credit, cost, running score
    ├── efc_adapter.py             EFC-ADAPTER — rank / retain / gate / stop, off the ledger (Part 2)
    └── demo.py                    end-to-end toy run tying all of the above together
```

## Quickstart

Zero external dependencies — Python 3.10+ stdlib only.

```bash
cd value_vault/code
python3 demo.py
```

`demo.py` scores a small toy trajectory's feedback events through the
four-gate mechanism, normalizes by raw cost and task demand, runs the
NRS-EFC redundancy tax on a repeated repair event (the loop-gate
0.95 → 0.45 example from Part 2), and finally runs EFC-ADAPTER's ROI
ranking and stop rule over a batch of candidate actions — printing a
ledger table at the end.

## What's an exact paper value vs. an illustrative default

`configs/efc_config.yaml` marks every constant `(paper)` or
`(illustrative)`. The gate structure and every published constant are
wired in exactly as reported: kappa = 10, the raw-cost weights
(lambda_tok=1.0, lambda_tool=0.35, lambda_time=0.10, lambda_op=0.04,
U_tok=1000), and the NRS-EFC ambiguity coefficient alpha_A = 0.35 are all
paper values, fixed across every experiment. Two things are **not**
published and are flagged as illustrative placeholders you should replace
with your own calibration before trusting the output:

- **`estimated_efc.py`'s `theta`/`theta0`** — the paper calibrates these on
  a held-out calibration split; it reports the *nine features* the
  estimator reads (checker fired, checker scope, tool-result reference,
  plan change, memory retention, repeated-error avoidance, observation
  consistency, subgoal progress, trace position) but not the fitted
  weights. Fit `theta` on your own labeled traces.
- **`nrs_efc.py`'s middle `STATUS_QUALITY` bands** — the source paper's
  appendix table is OCR-damaged past its two clean endpoints (a passed
  check = 1.00, an API error = 0.00). Only those two values and the
  repair-event loop-gate contrast (0.95 status-aware → 0.45 under NRS) are
  paper-verbatim; the intermediate status labels in this module are
  illustrative placeholders.

Everything else — the multiplicative four-gate product, the outcome-blind
discipline rule (the estimator never sees the final success label), the
task-demand formula, the eta/D_task split, and EFC-ADAPTER's four
behaviors (rank by ROI, retain to durable memory, gate self-evolution,
stop on saturated gain) — is wired exactly as the source note describes.

## The one-line geometry to remember

> A trajectory isn't one blob of spend — it's a ledger, and every entry has
> to clear four gates (informative, valid, non-redundant, retained) to earn
> any credit at all. Price the events, and you can stop paying for the
> ones that were never worth anything.
