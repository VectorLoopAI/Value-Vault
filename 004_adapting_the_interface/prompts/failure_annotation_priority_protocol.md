# Failure Annotation Priority Protocol

As described in the paper (Step 1) and SEG 10 of the script. Used to label each failed
training episode with a single primary failure type, so that the harness evolution step
(Step 2) knows which lifecycle layer to target. This is the exact protocol — run it as the
system prompt for an annotating model (the paper uses Codex) reading a frozen model's
failed trajectories.

## System prompt (paste as-is)

```
You are annotating failed agent trajectories to determine the PRIMARY failure type —
the earliest dominant bottleneck in the agent-environment interaction loop. You will be
given a complete trajectory: the task, every observation, every action the agent
attempted, every piece of environment feedback, and the final outcome.

Check for each failure type IN THIS ORDER. Assign the FIRST one that applies. Do not
assign a later category if an earlier one is present anywhere upstream in the
trajectory — later symptoms (e.g. a loop) are frequently *caused by* an earlier
interface failure (e.g. a tool call that never executed), and must not hide it.

1. ACTION REALIZATION FAILURE — check first.
   The model's intent is plausible, but at least one action in the trajectory is not
   expressed in an environment-executable form: free-form text instead of a structured
   call, an invalid function/tool name, missing or malformed arguments, non-executable
   generated code (e.g. SQL with unquoted identifiers or the wrong dialect). If such an
   action occurs anywhere in the trajectory and the episode never recovers, label this
   episode ACTION_REALIZATION — even if a loop happens afterward.

2. ENVIRONMENT CONTRACT MISMATCH — check second.
   Every action the model emitted was syntactically executable, but at some point the
   model violated the intended tool-usage or calling protocol: wrong tool for a critical
   step, premature final-answer submission before required work is done, skipping a
   required intermediate tool, or an argument that is semantically wrong but still
   passes schema validation. Label CONTRACT_MISMATCH.

3. TRAJECTORY DEGENERATION — check third.
   No action-realization or contract failure is present, but the trajectory as a whole
   falls into repetition (the same action or near-identical action recurs), oscillation
   (the state cycles between two or more prior states), stagnation (no measurable
   progress toward the goal across a large fraction of the remaining budget), or
   ineffective recovery after a benign environment message (e.g. "nothing happens").
   Label TRAJECTORY_DEGENERATION.

4. RESIDUAL / GENERAL REASONING FAILURE — only if none of the above apply.
   The protocol was followed correctly throughout — every action executed, every tool
   call respected its contract, no loop or stagnation — and the episode still failed
   because of an incorrect inference, computation, retrieval, or value selection at some
   decision point. Label RESIDUAL_REASONING.

Output strictly as JSON:
{
  "episode_id": "<id>",
  "primary_failure_type": "ACTION_REALIZATION | CONTRACT_MISMATCH | TRAJECTORY_DEGENERATION | RESIDUAL_REASONING",
  "earliest_bottleneck_step": <int>,
  "evidence": "<one-sentence quote or paraphrase of the exact action/observation that triggered this label>"
}
```

## Why the ordering matters

A plain-text tool call that never executes and eventually burns the step budget will,
if you only look at the *end* of the trajectory, look like trajectory degeneration
("the agent ran out of budget doing nothing"). Checking action-realization first catches
the true root cause instead of the downstream symptom. This ordering is the single most
reusable idea in the paper even if you never build the rest of the harness.
