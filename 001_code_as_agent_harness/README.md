# 001 — Code as Agent Harness

Companion Value Vault for the Vector & Loop video **"Agent Harness: The Blind Spot in
Every Multi-Agent Coder."**

Video: [embed/link placeholder — add the published YouTube URL here once uploaded]

## What this ships

The video's closing pitch (SEG 34) promises three things "in the Value Vault." Here
they are:

| Asset | File | What it is |
|---|---|---|
| Three-layer diagram + four properties | `harness_architecture.md` | Reference doc: the Interface / Mechanisms / Scaling layers, the executable / inspectable / stateful / governed properties, and the four-level shared-state-formality ladder (file-only → repository-based → execution-based → blackboard) from the source survey. |
| Permission-tier checklist | `permission_tiers.yaml` | A loadable policy config for the three-tier permission model (read-only / sandbox-edit / full-access) plus the pre-use/post-use tool lifecycle hooks described in SEG 14 and SEG 16. |
| Plan-Execute-Verify template | `pev_loop.py` | A runnable, stdlib-only Python skeleton implementing the PEV loop (contract formation → sandboxed execution → deterministic verification), wired to the same permission tiers and hooks. |

## Quickstart

```bash
# no dependencies beyond the Python 3.9+ standard library
python pev_loop.py
```

Expected output: a telemetry trace (`plan -> pre-use -> execute -> post-use -> verify
-> done`) ending in `PASS`, produced by an actual sandboxed subprocess run against a
real assertion — not a mock.

To adapt it to your own stack:

1. Replace `demo_contract` in `pev_loop.py` with your own `ChangeContract` (target
   file, intended code, and a validation command that really runs your test suite).
2. Point `permission_tiers.yaml` at your actual tool surface — fill in
   `allowed_operations` with your real tool names.
3. Wire `pre_use_hook` / `post_use_hook` to your actual permission and telemetry
   backends (the demo versions are minimal stand-ins so the script runs standalone,
   with no external services required).
4. Never let a `FULL_ACCESS` contract execute without a live human-approval channel —
   `pev_loop.py` refuses to run one in the demo on purpose (see the `PermissionError`
   raised in `execute()`). That refusal is intentional, not a bug to work around.

## Source

Survey: *"Code as Agent Harness: Toward Executable, Verifiable, and Stateful Agent
Systems"* (UIUC / Meta / Stanford, 2026).
Paper repo: https://github.com/YennNing/Awesome-Code-as-Agent-Harness-Papers

## Next in the series

Video 002, "Production Agent Architecture Methodology," builds directly on this: the
stochastic/deterministic boundary and the pattern catalog for where to spend the
"agent budget" inside the harness this video defines.
