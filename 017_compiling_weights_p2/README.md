# 017 — Compiling weights Part 2: see Part 1's Value Vault

This episode (Part 2 of the "compile the agentic workflow, delete the
orchestrator" two-parter — and the Series A finale) shares its Value Vault
with **Part 1** — the procedure-graph formalism, the four-step compile
pipeline, and every data table discussed across both videos live in one
place, not duplicated per part:

    ../../016_compiling_weights_p1/value_vault/

**Part 1 video:** https://www.youtube.com/watch?v=ADirjzsva4E
**Part 2 video:** https://www.youtube.com/watch?v=8BecqKFZJgc

Source paper: *"Compiling Agentic Workflows into LLM Weights: Near-Frontier
Quality at Two Orders of Magnitude Less Cost"* — Simon Dennis, Rivaan
Patil, Kevin Shabahang, Hao Guo (i14, University of Melbourne, 2026).
arXiv:2605.22502 [cs.AI]. **The paper prints no repository URL** — Appendix
A references "the repository" for full unedited transcripts but gives no
link; there is no upstream code to point to.

If you're looking for this episode's own numbers — the 55-node insurance
procedure (6 decision hubs, 2,381 unique acyclic paths), the 92–98%
in-context quality the 8B compiled model reaches there, the failure-rate
split (5.5% vs. 24.0% on travel; 9.0% vs. 17.0% on insurance), the compound
cost table (128x / 296x / 462x cheaper as node count grows), the recompile
timeline (30–50 minutes optimized), and the two honesty caveats (the ~87%
information-accuracy plateau and the judge-dependent quality range, 83–99%
GPT-4.1 vs. 82–102% Claude) — those are argued in the video itself and
reproduced in `code/demo.py` in Part 1's folder (linked above), which walks
through every headline claim from both parts against the paper's own
tables.
