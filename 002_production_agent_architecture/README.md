# 002 — Production Agent Architecture: the stochastic-deterministic boundary

Companion assets for the Vector & Loop video **"LLM Agent Architecture: The Seam Nobody Names."**

**Video:** [link placeholder — added after upload]

Source paper: *"A Methodology for Selecting and Composing Runtime Architecture Patterns for
Production LLM Agents"* — Vasundra Srinivasan, Stanford School of Engineering (May 2026).
Companion repo: https://github.com/vasundras/agent-runtime-patterns

## What this is

The video names the **stochastic-deterministic boundary (SDB)** — the seam in an agent runtime
where an LLM proposal becomes a system action (proposer → verifier → commit → reject) — and walks
a six-pattern catalog for the three concerns every agent runtime must answer: **Coordination**,
**State**, **Control**.

This folder contains runnable reference implementations of all six patterns, the five-step
selection methodology as code (the spine-decision predicate), the quarterly drift-diagnostic
procedure, and the six-line ADR template the video promises up top.

```
value_vault/
├── README.md                      (this file)
├── adr_template.md                 six-line Architecture Decision Record template
├── spine_decision_predicate.py     Step 2 of the methodology as a runnable predicate
├── diagnostic_procedure.py         quarterly drift diagnostic (functional / replay-divergence / variance)
└── patterns/
    ├── p1_hierarchical_delegation.py
    ├── p2_scatter_gather_saga.py
    ├── p3_event_driven_sequencing.py
    ├── p4_supervisor_gate.py
    ├── p5_shared_state_machine.py
    └── p6_human_in_the_loop.py
```

## Quickstart

Everything here is dependency-free stdlib Python (3.10+) so you can drop it straight into a
prototype and swap in your own store/queue/LLM client.

```bash
cd value_vault

# Run each pattern's self-test / demo
python3 patterns/p5_shared_state_machine.py
python3 patterns/p4_supervisor_gate.py
python3 patterns/p1_hierarchical_delegation.py
python3 patterns/p2_scatter_gather_saga.py
python3 patterns/p3_event_driven_sequencing.py
python3 patterns/p6_human_in_the_loop.py

# Run the Step-2 spine decision predicate against a few example workloads
python3 spine_decision_predicate.py

# Run the quarterly drift-diagnostic procedure against a sample failure batch
python3 diagnostic_procedure.py
```

Fill in `adr_template.md` for your own workload — that's the six-line artifact the video builds
up to: Runtime class, Spine, Coordination, Control, Sequence, Date/model version, each row naming
the pattern, the predicate that fired, and the failure signature you'd expect if you picked wrong.

## The one-line geometry to remember

> State is the spine. Coordination wraps it. Control bounds it.

You don't pick one pattern — you build at the intersection of the three concerns, per workload.
