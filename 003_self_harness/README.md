# 003 — Self-Harness: Harnesses That Improve Themselves

Video: [embed/link placeholder — add the published YouTube URL here once live]

This folder reproduces the mechanism explained in the video: a **three-stage loop**
(Weakness Mining → Harness Proposal → Proposal Validation) that lets a fixed model
rewrite its own agent harness — no stronger external model, no human engineer.
Source paper: *"Self-Harness: Harnesses That Improve Themselves"* — Hangfan Zhang,
Shao Zhang, Kangcong Li, Chen Zhang, Yang Chen, Yiqun Zhang, Lei Bai, Shuyue Hu
(Shanghai Artificial Intelligence Laboratory, 2026 preprint). No public code
repository is listed for Self-Harness itself; the paper's initial harness is built
on the open-source DeepAgent SDK (github.com/langchain-ai/deepagents). Everything
in this folder is re-derived from the paper's algorithm description and the video's
script — there is no first-party repo to copy from.

## What's in here

| File | What it is |
|---|---|
| `initial_harness.yaml` | The deliberately minimal starting harness from the paper's experimental setup — system prompt, tool set, and the declared "editable surfaces" Self-Harness is allowed to touch. |
| `weakness_mining.py` | Runnable Python implementing Stage 1 — clusters failed execution traces by the `(c, q, m)` failure signature (terminal cause, causal behavior status, exposed mechanism) and ranks clusters by support + actionability. Two failures only merge if they agree on all three fields. |
| `acceptance_rule.py` | Runnable Python implementing Stage 3's promotion decision: `Δ_in ≥ 0 AND Δ_ho ≥ 0 AND max(Δ_in, Δ_ho) > 0`, plus the stochastic-evaluation aggregation (repeat + average before applying the rule) described in the paper. |
| `accepted_edits/minimax_bootstrap_instruction.yaml` | The MiniMax M2.5 case-study edit — bootstrap instruction rewritten from "identify the smallest relevant edit surface" to "identify the required output artifact and create an initial version as early as possible." |
| `accepted_edits/qwen_tool_error_middleware.yaml` | The Qwen3.5 case-study edit — a tool-error-triggered system prompt (middleware) that fires on any tool failure and redirects the agent to recover/recreate the required artifact instead of hammering or deleting it. This is the exact fix behind the `extract-elf` recovery shown in the video. |
| `accepted_edits/glm5_verification_constraint.yaml` | The GLM-5 case-study edit — persistent shell-session tool/path state, plus a verification-stage constraint that forces a hard stop-exploring/start-implementing transition once artifacts are overdue. |

## Quickstart

```bash
# 1. Cluster a batch of failure traces into evidence bundles (Stage 1)
python weakness_mining.py

# 2. Check whether a candidate harness edit should be promoted (Stage 3)
python acceptance_rule.py
```

Both scripts run standalone with the sample data embedded at the bottom of each
file (`if __name__ == "__main__":`) — swap in your own traces / split results to
apply the loop to your own agent stack. To reproduce the paper's benchmark
setup, point your harness at `initial_harness.yaml`, run it against your own
held-in/held-out task splits, feed the failures through `weakness_mining.py`,
have your model (in a "proposer" role) generate candidate edits against the
`editable_surfaces` list in `initial_harness.yaml`, then gate every candidate
through `acceptance_rule.py` before merging.

## The acceptance rule (memorize this one)

```
accept(Δ_in, Δ_ho) := (Δ_in >= 0) AND (Δ_ho >= 0) AND (max(Δ_in, Δ_ho) > 0)
```

Promote a harness edit only if it doesn't hurt either split, and it meaningfully
helps at least one. No trading held-in gains for held-out losses, even if total
pass count technically rises.
