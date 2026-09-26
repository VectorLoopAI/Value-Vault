# 015 — PreAct Part 2: see Part 1's Value Vault

This episode (Part 2 of the "compile once / verify twice" PreAct two-parter)
shares its Value Vault with **Part 1** — the program schema, the run-time
replayer, the store-time verify gate, and every data table discussed across
both videos live in one place, not duplicated per part:

    ../../014_preact_p1/value_vault/

**Part 1 video:** https://www.youtube.com/watch?v=Drv9UDuMkW8
**Part 2 video (this one):** https://www.youtube.com/watch?v=NpQuI26iSww

Source paper: *"PreAct: Computer-Using Agents That Get Faster On Repeated
Tasks"* — Bojie Li (Pine AI)

If you're looking for this episode's own numbers — the store-time double
gate (§3.3), the Table 2 verify-gate ablation (2.6 / 2.6 / 1.75 tasks across
Android, OSWorld, and WebArena), Table 3's five reproducible coverage-100%/
score-0 programs, the Muscle-Mem head-to-head (PreAct loses 2.0 vs 6.25,
then ties exactly at 6.25 after a one-line cache-miss fallback fix), the
embedding-retriever-beats-the-LLM-selector negative result (100% vs 75.6%),
and the out-of-distribution generalization headwind (55.6% vs ~67% cold) —
those are argued in the video itself and reproduced in `code/demo.py` in
Part 1's folder (linked above), which recomputes every headline claim from
both parts against the paper's own tables, including replaying the exact
7-state "Emilia Gonzalez program" from Part 1 both ways: coverage 100% with
the goal met, and coverage 100% with it not.
