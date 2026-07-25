# Agent Harness Architecture — Reference Sheet

Companion to Vector & Loop video 001. Faithfully condensed from
`backlog/001_code_as_agent_harness.md`, the source note for the UIUC/Meta/Stanford
survey "Code as Agent Harness: Toward Executable, Verifiable, and Stateful Agent
Systems."

## The reframe

Code is not just the artifact an LLM produces (the diff, the patch, the answer). Code
is the **harness** — the software layer wrapped around the model: tools, sandboxes,
memory, validators, permission boundaries, the execution loop. It's what turns a
stateless model into something that can act over a long horizon.

Three components of a harness:
- **Model-internal capabilities** — the model's own reasoning, planning, evaluation.
- **System-provided infrastructure** — tools, APIs, sandboxes, telemetry humans build.
- **Agent-initiated code artifacts** (underexplored) — tests, throwaway tools, skills
  the agent writes for *itself* mid-task, reshaping its own execution environment.

## The three layers

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1 — INTERFACE                                          │
│ What medium connects the model to its task environment?      │
│   • Code for reasoning     (Program-of-Thoughts, Lean proofs,│
│                              generate-execute-verify-refine)  │
│   • Code for acting        (Code as Policies, Voyager,        │
│                              robot/GUI actions that can fail  │
│                              silently — no exception raised)  │
│   • Code for env modeling  (SWE-bench: repo-level unit-test   │
│                              execution grades the agent, not  │
│                              textual correctness)             │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2 — MECHANISMS                                          │
│ How does the harness decide what to run, hold state, correct  │
│ failures?                                                      │
│   • Planning as harness control (PLAN.md as a git-versioned    │
│     control object that survives a context reset)              │
│   • Memory as state management (not a bigger context window,   │
│     not a vector DB — what stays active / gets compacted /     │
│     gets offloaded)                                            │
│   • Tool lifecycle control (pre-use hooks: permission check,    │
│     argument validation; post-use hooks: sanitize, log, verify) │
│   • The Plan-Execute-Verify (PEV) loop — the unifying frame:    │
│       PLAN (contract formation) -> EXECUTE (sandboxed,          │
│       permissioned) -> VERIFY (deterministic sensors + human    │
│       gate). Acts as a cybernetic governor on the model.        │
│   • Agentic Harness Engineering — optimizing the operating       │
│     environment itself, powered by deep telemetry, via a meta-  │
│     level Evolution Agent (observe -> diagnose -> propose ->    │
│     evaluate -> promote), itself subject to PEV.                │
├─────────────────────────────────────────────────────────────┤
│ LAYER 3 — SCALING                                              │
│ What happens when one agent isn't enough?                      │
│   • Role specialization (independent Test Designer + a          │
│     deterministic, non-LLM Test Executor — avoids mode collapse)│
│   • Interaction modes (critique-and-repair is dominant;          │
│     adversarial validation — a fuzzer that demonstrates a crash  │
│     instead of arguing about correctness — is sharper)           │
│   • Shared-state formality ladder (below)                        │
└─────────────────────────────────────────────────────────────┘
```

## The four-level shared-state-formality ladder (Layer 3's core finding)

1. **File-only / implicit** — state reconstructed from conversation history each
   invocation. The majority of surveyed systems (ChatDev, MetaGPT, MapCoder, SEW,
   CodePori...). State divergence is invisible and undetectable by design. **This is
   the blind spot.**
2. **Repository-based** — git-diff-tracked evolution memory, navigation tools
   (`get_tree_structure`, `go_to_definition`, `code_search`). SyncMind is the only
   surveyed system to formally define ground-truth state `S_k` vs. agent belief state
   `B_k` and measure the divergence `|B_k − S_k|`.
3. **Execution-based** — "the state is not what the code looks like, it's what the
   code does." AgentCoder, AutoSafeCoder, QualityFlow, EvoMAC, CANDOR live here.
4. **Blackboard / shared-state** — a true persistent, explicitly-scheduled shared
   store. L2MAC's Control Unit is called out as "the most principled blackboard in the
   literature" — and notably, it also has the *simplest* topology (a plain sequential
   chain). Topology complexity inversely correlates with state formality: systems
   without a formal substrate compensate with elaborate adaptive orchestration.

## The permission-tier model (Layer 2, Execute stage)

| Tier | Scope | Human gate |
|---|---|---|
| 1 — Read-only | browsing, retrieval, static inspection | no |
| 2 — Sandbox-edit | local patching, running tests, isolated dependency installs | no |
| 3 — Full-access | network, credentials, deployment, destructive filesystem ops, git-history rewrite | **mandatory, non-negotiable** |

An agent earns each ring — it never starts at the center. See `permission_tiers.yaml`
for a loadable version of this table plus the tool lifecycle hooks that enforce it.

## The four closing properties

The survey's own definition of what a good agent harness looks like:

- **Executable** — outputs become verifiable operations.
- **Inspectable** — computation becomes readable, structured traces.
- **Stateful** — progress persists across steps, in a modifiable form.
- **Governed** — permissioned, gated, auditable. *(The property added specifically to
  answer the blind spot — you don't fix state divergence with a smarter model, you fix
  it with a harness that holds real, formal, shared state and governs who can change
  it.)*

## Open problems worth tracking

1. Harness-level evaluation (most benchmarks only measure end-task success).
2. Semantic verification beyond "green test" — a passing test is a *sample* of the
   spec, not the whole spec. Proposal: every accepted action carries an evidence
   bundle (checks run, assumptions held, untested regions, remaining risk).
3. Self-evolving harnesses without regression — every harness mutation should carry a
   *change contract*: component changed, failure mode targeted, predicted gain,
   invariants preserved, falsifying evaluation, rollback path.
4. Transactional shared program state — today's blackboards sync artifacts, not
   assumptions; needs read/write sets, version dependencies, semantic conflict
   resolution (git can merge two files, not two agents who disagree about the goal).
5. Multimodal harnesses — GUI/robotic agents need grounding contracts (bounding box,
   object ID, frame index) and calibrated, non-binary feedback.

Source: "Code as Agent Harness: Toward Executable, Verifiable, and Stateful Agent
Systems" (UIUC / Meta / Stanford, 2026). Paper repo:
https://github.com/YennNing/Awesome-Code-as-Agent-Harness-Papers
