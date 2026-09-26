"""
data_tables.py -- every published number named in Part 1 and Part 2,
transcribed from backlog/010_preact.md (itself cross-checked against the
paper's tables) and both episodes' script.md.

Tagging convention:
  (paper, verified)  -- copied from a paper table/figure, or a value the
                        backlog note independently re-derived and confirmed
                        against the paper's own prose.
  (paper, qualitative) -- the paper states this only descriptively, with no
                        numeric multiplier (used for the Android/OSWorld
                        replay-speed claims -- see SCOPED_SPEEDUP_NOTE).

Deliberately NOT included: Table 1's fine-grained cells. The backlog note
flags Table 1 as badly OCR-mangled/reconstructed from surrounding prose --
per instruction, its fine-grained cells are never used, here or anywhere in
this Value Vault or the packaging.

Nothing in this file is invented.
"""

# ---------------------------------------------------------------------------
# PART 1 -- replay works and is fast.
# ---------------------------------------------------------------------------

ANDROID_COLD_WARM_BY_SEED = {
    # (paper, verified) -- tasks solved out of 15, per Gemini-3-Flash seed
    42:   {"cold": 10, "warm": 11},
    100:  {"cold": 9,  "warm": 11},
    1337: {"cold": 9,  "warm": 10},
}
ANDROID_COLD_WARM_MEAN = {"cold": 9.33, "warm": 10.67}          # (paper, verified)
ANDROID_COLD_WARM_DELTA_TASKS = 1.33                            # (paper, verified)
ANDROID_COLD_WARM_DELTA_PP = 8.9                                # (paper, verified)
ANDROID_EVERY_SEED_IMPROVED = True                               # (paper, verified) -- no seed regressed

SEED42_COMPOSITION = {
    # (paper, verified) -- of the 13 tasks that clear setup on seed 42
    "tasks_clearing_setup": 13,
    "cold_solved_by_fresh_reasoning": 13,
    "warm_shifted_to_replay_or_hybrid": 8,
}

SCOPED_SPEEDUP_NOTE = (
    "8.5-13x faster is the WebArena wall-clock measurement specifically -- a "
    "served replay against the corresponding fresh-agent solve (paper, Figure 1). "
    "Android and OSWorld replay speed are reported only QUALITATIVELY -- "
    "'near-free,' 'finishes in seconds' -- the paper gives NO separate multiplier "
    "for either platform. Never state 8.5-13x as a universal cross-platform figure."
)
WEBARENA_WALL_CLOCK_SPEEDUP_RANGE_X = (8.5, 13.0)                # (paper, verified) -- WebArena ONLY, see note above
ANDROID_OSWORLD_REPLAY_SPEED_CLAIM = "near-free / finishes in seconds"  # (paper, qualitative) -- no multiplier given

COMPILE_AND_VERIFY_OVERHEAD_PCT = {"android": 162, "osworld": 217}       # (paper, verified) -- one-time, per stored program
MEDIAN_VERIFY_REPLAY_VS_BASE_SECONDS = {
    "android":  {"verify_replay": 76,  "base_solve": 47},   # (paper, verified)
    "osworld":  {"verify_replay": 141, "base_solve": 65},   # (paper, verified)
}

CROSS_MODEL_REPLICATION = {
    # (paper, verified) -- same Android subset, Gemini 3 Flash vs Claude Sonnet 4.6
    "success_rate_pct": 73.3,
    "tasks_solved_of_15": 11,
    "identical_across_both_models_and_all_3_seeds": True,
    "stable_failures": ["BrowserDraw", "SystemBrightnessMax", "SystemWifiTurnOn"],
    "failure_cause": "harness-deterministic UI properties, not agent reasoning -- a canvas not exposed in the accessibility tree, a brightness slider that rejects scroll, a stale status-bar Wi-Fi icon",
}

# ---------------------------------------------------------------------------
# PART 2 -- what happens when nothing checks what gets remembered.
# ---------------------------------------------------------------------------

WEBARENA_GATE_REJECTION_RATE_PCT = 83   # (paper, verified)

CORPUS_AUDIT = {
    # (paper, verified)
    "programs_audited": {"android": 58, "osworld": 16, "webarena": 7},
    "android_missing_navigate_back_pct": 28,
    "webarena_inspecting_dynamic_state_pct": 100,
}

# Table 2 -- the verify-gate ablation, 2x2 (cold/warm x gate on/off), all
# three platforms. (paper, verified)
VERIFY_GATE_ABLATION_TABLE2 = {
    "android":  {"delta_gate_on": 1.2,  "delta_gate_off": -1.4,  "gate_gain_tasks": 2.6},
    "osworld":  {"delta_gate_on": 0.2,  "delta_gate_off": -2.4,  "gate_gain_tasks": 2.6},
    "webarena": {"delta_gate_on": -4.0, "delta_gate_off": -5.75, "gate_gain_tasks": 1.75},
}
GATE_EFFECT_DIRECTIONAL_NOTE = (
    "13 of 14 paired runs point the same way (the 14th, a WebArena rep, ties). "
    "The paper calls this a directional lower bound, not an independent-samples "
    "significance claim -- within-platform reps are correlated."
)

# Table 3 -- the five reproducible "coverage 100% / score 0" programs under
# gate-off. (paper, verified)
LOSSY_PROGRAMS_TABLE3 = [
    {"platform": "Android",  "program": "ContactsAddContact",  "failure": "replay completes; no contact written -- a stale field left the name blank"},
    {"platform": "Android",  "program": "MarkorCreateFolder",  "failure": "folder not created at the expected path"},
    {"platform": "OSWorld",  "program": "Chrome history-clean", "failure": "browser state mismatches the goal"},
    {"platform": "OSWorld",  "program": "LibreOffice Calc formula", "failure": "wrong cell formula written"},
    {"platform": "OSWorld",  "program": "LibreOffice Calc chart",   "failure": "chart properties mismatch"},
]
WEBARENA_GATE_OFF_TOTAL_COLLAPSE = "48 of 48 gate-off warm replays score 0"   # (paper, verified)

# Table 4 -- the Muscle-Mem head-to-head, WebArena 12-task subset, n=4.
# (paper, verified)
MUSCLE_MEM_HEAD_TO_HEAD = {
    "muscle_mem_warm_sr": 6.25,          # out of 12
    "preact_gate_on_before_fix_warm_sr": 2.0,   # out of 12 -- "more than 3x worse"
    "preact_gate_on_after_fix_warm_sr": 6.25,   # out of 12 -- exact match after the one-line cache-miss fallback
    "welch_t_test_p_after_fix": 0.84,
    "workflow_use_baseline_warm_sr": 0.0,        # per-task scripts, no verification -- behaves like gate-off, every rep
}

# What did NOT matter (Section 4.6) -- the negative-results section.
# (paper, verified)
SELECTOR_COMPARISON = {
    "embedding_retriever_correct_family_retrieval_pct": 100.0,
    "embedding_retriever_mis_routing_pct": 0.0,
    "agentic_llm_selector_functional_accuracy_pct": 75.6,
    "kept_llm_selector_anyway_because": "interpretable reasoning logs -- not because it retrieves better",
}
PROMPT_WORDING_NOTE = "the 73.3% Android SR uses the verbatim upstream T3A prompt, zero PreAct-specific additions"  # (paper, verified)
RUNTIME_GUARDRAILS_NOTE = {"cold_identical": True, "warm_on": 11.0, "warm_off": 10.6, "verdict": "0.4-task gap, well within seed-level variance"}  # (paper, verified)
STEP_BUDGET_CAP = {"capped_mean": 9.8, "capped_std": 0.84, "uncapped_mean": 11.6, "uncapped_std": 0.55, "delta_tasks": 1.8, "verdict": "a deliberate latency/accuracy knob, not a neutral finding"}  # (paper, verified)

# Out-of-distribution generalization (Section 5.6, Appendix D) -- the honest
# negative result. Corpus built on OSWorld test_tiny (4 gate-stored programs),
# run on held-out tasks. (paper, verified)
OOD_GENERALIZATION = {
    "gate_stored_programs": 4,
    "held_out_tasks": 33,
    "held_out_domains": 9,
    "warm_ood_success_pct": 55.6,
    "cold_baseline_no_corpus_pct": 67,   # approximate, as stated in the paper's prose
    "drag_pp": 11,
    "cause": "mis-routed selector picks -- e.g. a Chrome history-clean program retrieved for a Thunderbird task, both queries sharing the word 'open'",
}

IDEMPOTENCY_LIMITATION = (
    "The gate works by literally re-running the candidate program -- safe in a "
    "resettable benchmark, not safe anywhere else. Re-running 'add contact "
    "Emilia Gonzalez' creates a second Emilia Gonzalez; re-running 'send the "
    "email' or 'submit the payment' duplicates the side effect instead of "
    "re-confirming the goal. Open alternatives (future work, not solved): a "
    "read-only end-state check, a sandboxed dry run, or a transactional rollback."
)

CLOSING_THESIS = "Store the program you run, and never keep one you have not checked."  # (paper, verbatim closing line)
