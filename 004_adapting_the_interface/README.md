# 004 — Adapting the Interface, Not the Model (LIFE-HARNESS)

Video: *LLM Agent Harness: Fix the Interface, Not the Model* — Vector & Loop
Watch: [VIDEO_LINK_PLACEHOLDER — filled in after upload]

Source paper: "Adapting the Interface, Not the Model: Runtime Harness Adaptation for
Deterministic LLM Agents" — Tianshi Xu†, Huifeng Wen†, Meng Li (Peking University, 2026;
† equal contribution). System name in the paper: **LIFE-HARNESS**. The paper states code
is available on the authors' GitHub but prints no explicit URL/arXiv ID in the body — this
folder is an independent, from-scratch reference reimplementation of the four-layer pattern
described in the paper, built for engineers who want to run the idea against their own agent
today rather than wait on upstream code.

## What this video built

The core claim: an LLM agent's failures on deterministic, rule-governed tasks (ALFWorld,
tau-bench, DBBench, OS) are rarely reasoning failures — they're interface failures. This
repo is a small, dependency-free Python package, `life_harness/`, that implements the four
lifecycle layers from the paper as a pluggable wrapper around *any* agent loop, without
touching model weights:

| Layer | Fires | File | Fixes |
|---|---|---|---|
| ❶ Environment Contract | before interaction | `life_harness/contract_layer.py` | contract mismatches — rewrites `C' = C ⊕ ΔC` |
| ❷ Procedural Skill | task-conditioning | `life_harness/skill_layer.py` | cold-start / missing task strategy — BM25 top-1 skill retrieval |
| ❸ Action Realization | pre-execution | `life_harness/action_realization_layer.py` | non-executable actions — validate / canonicalize / block |
| ❹ Trajectory Regulation | post-feedback | `life_harness/trajectory_regulation_layer.py` | loops, stagnation, budget burn — graduated escalation |

`life_harness/pipeline.py` wires all four into a single `step()` call and includes a toy
deterministic environment (`life_harness/demo_env.py`) so you can see every layer fire end
to end with `python -m life_harness.pipeline` — no benchmark install required. Swap in your
own environment's tool schemas, admissible-action set, and step function and the same four
layers apply.

Also included, extracted faithfully from the paper and the script:

- `prompts/failure_annotation_priority_protocol.md` — the exact priority-ordered failure
  annotation protocol (action-realization → contract → trajectory → residual-reasoning)
  used to label failed training episodes before any harness is written.
- `prompts/harness_evolution_constraints.md` — the safety-critical-code discipline the
  paper's Codex-driven evolution loop is held to (no test-label leakage, local/minimal
  edits, mandatory regression check).
- `configs/four_failure_modes.yaml` — the taxonomy definitions in one machine-readable file.
- `configs/example_airline_contract.yaml` — the tau-bench Airline `ΔC` contract and
  `book_reservation` guard described in the video (SEG 22).
- `configs/example_alfworld_subgoal_state_machine.yaml` — the ALFWorld WorldModel +
  subgoal state machine described in the video (SEG 23).

## Quickstart

```bash
cd 004_adapting_the_interface
python3 -m life_harness.pipeline
```

This runs the bundled demo: a frozen "model" (a scripted stand-in, since this repo ships
no model weights) attempts a few DBBench-style and ALFWorld-style actions. You'll see the
contract layer inject `ΔC` into the system prompt, the action-realization layer canonicalize
a malformed SQL call and block a non-executable one, the skill layer retrieve the single
best-matching skill by BM25, and the trajectory-regulation layer escalate a warning once it
detects a repeated action.

To point this at your own agent: replace `demo_env.py`'s `DemoEnv` with your environment's
`step(action)` function, populate `configs/*.yaml` with your own tool schemas / contract
deltas / skills, and call `HarnessPipeline.step(...)` around your existing action-selection
call — the four layers don't require retraining or fine-tuning anything.

## Failure-mode triage discipline (useful even without the full harness)

Even if you never build the full four-layer system, the priority-ordered annotation
protocol in `prompts/failure_annotation_priority_protocol.md` is a standalone debugging
habit: before you conclude "the model isn't smart enough," check — in this order —
whether the action was even executable, whether it violated the tool contract, whether the
trajectory degenerated into a loop, and only then whether it was a genuine reasoning error.
