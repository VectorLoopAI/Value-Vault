"""
demo.py -- recomputes the central mechanism of BOTH episodes against the
paper's own tables, using only state_machine.py + verify_gate.py +
data_tables.py. Zero external dependencies -- Python 3.10+ stdlib only.

Run: python3 demo.py
"""

from __future__ import annotations

from state_machine import CONTACTS_ADD_CONTACT, replay
from verify_gate import Corpus, select_or_fresh_solve, store_time_gate
from data_tables import (
    ANDROID_COLD_WARM_BY_SEED,
    ANDROID_COLD_WARM_MEAN,
    ANDROID_COLD_WARM_DELTA_TASKS,
    SEED42_COMPOSITION,
    SCOPED_SPEEDUP_NOTE,
    WEBARENA_WALL_CLOCK_SPEEDUP_RANGE_X,
    COMPILE_AND_VERIFY_OVERHEAD_PCT,
    CROSS_MODEL_REPLICATION,
    WEBARENA_GATE_REJECTION_RATE_PCT,
    CORPUS_AUDIT,
    VERIFY_GATE_ABLATION_TABLE2,
    GATE_EFFECT_DIRECTIONAL_NOTE,
    LOSSY_PROGRAMS_TABLE3,
    WEBARENA_GATE_OFF_TOTAL_COLLAPSE,
    MUSCLE_MEM_HEAD_TO_HEAD,
    SELECTOR_COMPARISON,
    OOD_GENERALIZATION,
    IDEMPOTENCY_LIMITATION,
    CLOSING_THESIS,
)


def part1_replay_the_emilia_gonzalez_program() -> None:
    print("=== PART 1 -- replaying the Emilia Gonzalez program (Listing 1) ===")

    # A screen sequence where every predicate genuinely matches AND the form
    # actually gets filled in -- the happy path.
    clean_run = {sid: True for sid in [s.id for s in CONTACTS_ADD_CONTACT.states]}
    result = replay(CONTACTS_ADD_CONTACT, clean_run)
    print(f"  Clean run   -> terminal_reached={result.terminal_reached}, "
          f"coverage={result.coverage:.0%}, states_visited={result.states_visited}")

    # A mismatch mid-replay -- e.g. the phone-type selector never appears.
    # Replay halts and hands off to the CUA fallback (paper, Section 3.2).
    mismatch_run = dict(clean_run)
    mismatch_run["phone_entered"] = False
    result2 = replay(CONTACTS_ADD_CONTACT, mismatch_run)
    print(f"  Mismatch run -> terminal_reached={result2.terminal_reached}, "
          f"halted_at={result2.halted_at!r}, coverage={result2.coverage:.0%} "
          f"(hands off to the CUA fallback here -- zero model calls until this exact point)")
    print()

    print(f"  Android cold->warm, 3 Gemini seeds: {ANDROID_COLD_WARM_BY_SEED}")
    print(f"  mean {ANDROID_COLD_WARM_MEAN['cold']} -> {ANDROID_COLD_WARM_MEAN['warm']} "
          f"(+{ANDROID_COLD_WARM_DELTA_TASKS} tasks, every seed improves)")
    print(f"  seed 42 composition: {SEED42_COMPOSITION}")
    print(f"\n  {SCOPED_SPEEDUP_NOTE}")
    print(f"  WebArena wall-clock speedup range: {WEBARENA_WALL_CLOCK_SPEEDUP_RANGE_X[0]}-"
          f"{WEBARENA_WALL_CLOCK_SPEEDUP_RANGE_X[1]}x (WebArena only)")
    print(f"  one-time compile-and-verify overhead: {COMPILE_AND_VERIFY_OVERHEAD_PCT}")
    print(f"  cross-model replication: {CROSS_MODEL_REPLICATION}\n")


def part2_the_lossy_program_the_gate_catches() -> None:
    print("=== PART 2 -- the SAME program, gate off vs gate on ===")

    # Screen predicates only check that the RIGHT FIELD IS VISIBLE at each
    # step -- not that the value actually landed. So a run where the
    # first-name value silently failed to commit still walks every state
    # cleanly. This is exactly the paper's "coverage 100% / score 0" failure,
    # reproduced structurally against the real 7-state program from Part 1.
    lossy_but_fully_covered = {sid: True for sid in [s.id for s in CONTACTS_ADD_CONTACT.states]}
    lossy_result = replay(CONTACTS_ADD_CONTACT, lossy_but_fully_covered)
    print(f"  Replay alone says: terminal_reached={lossy_result.terminal_reached}, "
          f"coverage={lossy_result.coverage:.0%}  <-- looks perfect")

    # The independent evaluator is what actually checks the goal -- and here
    # it reports the contact was never written (a stale field, per the paper).
    evaluator_scored_pass = False
    decision_off = store_time_gate(lossy_result, evaluator_scored_pass)
    print(f"  Store-time gate verdict: stored={decision_off.stored}")
    print(f"    reason: {decision_off.reason}\n")

    corpus = Corpus()
    corpus.upsert(CONTACTS_ADD_CONTACT, decision_off)
    print(f"  Corpus lookup after rejection: "
          f"{corpus.lookup(CONTACTS_ADD_CONTACT.dedup_signature)}  <-- gate DELETES a rejected candidate")
    next_run_action = select_or_fresh_solve(corpus, CONTACTS_ADD_CONTACT.dedup_signature)
    print(f"  Next run action (after the Table 4 cache-miss fix): {next_run_action}\n")

    # Now the good path: the evaluator confirms the contact really exists.
    clean_result = replay(CONTACTS_ADD_CONTACT, lossy_but_fully_covered)
    decision_on = store_time_gate(clean_result, evaluator_scored_pass=True)
    corpus.upsert(CONTACTS_ADD_CONTACT, decision_on)
    print(f"  Store-time gate verdict (evaluator now confirms the goal): stored={decision_on.stored}")
    print(f"  Corpus lookup: program present = "
          f"{corpus.lookup(CONTACTS_ADD_CONTACT.dedup_signature) is not None}\n")


def part2_ablation_and_head_to_head() -> None:
    print("=== PART 2 -- Table 2 ablation, Table 3 lossy programs, Muscle-Mem head-to-head ===")
    print(f"  WebArena gate rejection rate: {WEBARENA_GATE_REJECTION_RATE_PCT}%")
    print(f"  Corpus audit: {CORPUS_AUDIT}\n")

    for platform, row in VERIFY_GATE_ABLATION_TABLE2.items():
        print(f"  {platform:9s} gate ON {row['delta_gate_on']:+.2f} tasks | "
              f"gate OFF {row['delta_gate_off']:+.2f} tasks | gate's gain = {row['gate_gain_tasks']} tasks")
    print(f"  {GATE_EFFECT_DIRECTIONAL_NOTE}\n")

    print("  Table 3 -- five reproducible coverage=100%/score=0 programs (gate-off):")
    for row in LOSSY_PROGRAMS_TABLE3:
        print(f"    [{row['platform']:8s}] {row['program']:22s} -- {row['failure']}")
    print(f"  WebArena: {WEBARENA_GATE_OFF_TOTAL_COLLAPSE}\n")

    m = MUSCLE_MEM_HEAD_TO_HEAD
    print(f"  Muscle-Mem warm SR: {m['muscle_mem_warm_sr']}/12")
    print(f"  PreAct gate-ON warm SR BEFORE the fallback fix: {m['preact_gate_on_before_fix_warm_sr']}/12  <-- they lost")
    print(f"  PreAct gate-ON warm SR AFTER the fallback fix:  {m['preact_gate_on_after_fix_warm_sr']}/12  "
          f"(p ~= {m['welch_t_test_p_after_fix']}, statistically indistinguishable from Muscle-Mem)")
    print(f"  Workflow-Use (no verification) warm SR: {m['workflow_use_baseline_warm_sr']}/12 in every rep\n")


def part2_what_did_not_matter_and_limits() -> None:
    print("=== PART 2 -- what did NOT matter, and where the system runs out ===")
    s = SELECTOR_COMPARISON
    print(f"  Embedding retriever: {s['embedding_retriever_correct_family_retrieval_pct']}% correct-family "
          f"retrieval, {s['embedding_retriever_mis_routing_pct']}% mis-routing")
    print(f"  Agentic LLM selector: {s['agentic_llm_selector_functional_accuracy_pct']}% functional accuracy")
    print(f"  They kept the LLM selector anyway -- {s['kept_llm_selector_anyway_because']}\n")

    o = OOD_GENERALIZATION
    print(f"  OOD generalization: {o['gate_stored_programs']} gate-stored programs -> "
          f"{o['held_out_tasks']} held-out tasks across {o['held_out_domains']} domains")
    print(f"  warm-OOD success = {o['warm_ood_success_pct']}% vs cold-no-corpus baseline ~{o['cold_baseline_no_corpus_pct']}% "
          f"-- the corpus made things WORSE by ~{o['drag_pp']}pp")
    print(f"  cause: {o['cause']}\n")

    print(f"  Idempotency limitation: {IDEMPOTENCY_LIMITATION}\n")
    print(f"  Closing thesis: \"{CLOSING_THESIS}\"")


if __name__ == "__main__":
    part1_replay_the_emilia_gonzalez_program()
    part2_the_lossy_program_the_gate_catches()
    part2_ablation_and_head_to_head()
    part2_what_did_not_matter_and_limits()
