"""
data_tables.py -- every headline number named on-camera across both PreAct
episodes, source-tagged to backlog/010_preact.md. Nothing here is invented;
cells not present in the script/backlog note are simply absent, not guessed.
Table 1 (the comparison-of-prior-systems table) is deliberately excluded --
the backlog note flags it as OCR-reconstructed, so its fine-grained cells
are never used for a specific claim.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Part 1 -- Android cold -> warm (3 Gemini seeds)
# ---------------------------------------------------------------------------
ANDROID_COLD_WARM = {
    42: (10, 11),
    100: (9, 11),
    1337: (9, 10),
}  # (cold tasks solved, warm tasks solved), out of 15
ANDROID_COLD_WARM_MEAN = (9.33, 10.67)  # +1.33 tasks, +8.9 pp

# ---------------------------------------------------------------------------
# Part 1 -- the one-time compile-and-verify cost
# ---------------------------------------------------------------------------
COMPILE_VERIFY_OVERHEAD_PCT = {
    "AndroidWorld": 162,
    "OSWorld": 217,
}
MEDIAN_VERIFY_REPLAY_S = {"AndroidWorld": (76, 47)}  # (verify-replay, base solve)

# ---------------------------------------------------------------------------
# Part 1 -- WebArena wall-clock speedup. SCOPED: this multiplier is measured
# on WebArena only. The paper reports Android/OSWorld replay as qualitatively
# "near-free" with no separate multiplier -- do not extend this range to them.
# ---------------------------------------------------------------------------
WEBARENA_WALLCLOCK_SPEEDUP_X = (8.5, 13.0)

# ---------------------------------------------------------------------------
# Part 1 -- cross-model replication (same Android subset)
# ---------------------------------------------------------------------------
CROSS_MODEL_SR = {
    "Gemini 3 Flash": 11 / 15,
    "Claude Sonnet 4.6": 11 / 15,
}
STABLE_FAILURES_BOTH_MODELS = [
    "BrowserDraw", "SystemBrightnessMax", "SystemWifiTurnOn",
]

# ---------------------------------------------------------------------------
# Part 2 -- Table 2: the verify-gate ablation, gate ON vs gate OFF
# ---------------------------------------------------------------------------
VERIFY_GATE_ABLATION = {
    # platform: (delta_gate_on, delta_gate_off, gate_gain)
    "AndroidWorld (Gemini)": (1.2, -1.4, 2.6),
    "OSWorld (Claude)": (0.2, -2.4, 2.6),
    "WebArena (Claude)": (-4.0, -5.75, 1.75),
}
WEBARENA_GATE_REJECTION_RATE = 0.83  # ~83% of compiled candidates rejected

# ---------------------------------------------------------------------------
# Part 2 -- Table 3: reproducible coverage=100% / score=0 programs (gate-off)
# ---------------------------------------------------------------------------
LOSSY_PROGRAMS_TABLE3 = [
    {"platform": "AndroidWorld", "program": "ContactsAddContact",
     "coverage": 1.0, "score": 0.0,
     "failure": "stale field left the name blank -- no contact written"},
    {"platform": "AndroidWorld", "program": "MarkorCreateFolder",
     "coverage": 1.0, "score": 0.0, "failure": "folder created at the wrong path"},
    {"platform": "OSWorld", "program": "Chrome-history-clean",
     "coverage": 1.0, "score": 0.0, "failure": "browser state mismatch"},
    {"platform": "OSWorld", "program": "LibreOffice Calc formula",
     "coverage": 1.0, "score": 0.0, "failure": "wrong cell formula (5/5 reps)"},
    {"platform": "OSWorld", "program": "LibreOffice Calc chart",
     "coverage": 1.0, "score": 0.0, "failure": "wrong chart properties (4/5 reps)"},
]
WEBARENA_GATE_OFF_TOTAL_COLLAPSE = "48 of 48 warm replays scored 0"

# ---------------------------------------------------------------------------
# Part 2 -- Muscle-Mem head-to-head (WebArena, 12-task, n=4), before/after fix
# ---------------------------------------------------------------------------
MUSCLE_MEM_HEAD_TO_HEAD = {
    "muscle_mem_warm_sr": 6.25 / 12,
    "preact_gate_on_before_fallback": 2.0 / 12,
    "preact_gate_on_after_fallback": 6.25 / 12,
    "p_value_after_fallback": 0.84,
}

# ---------------------------------------------------------------------------
# Part 2 -- what didn't matter (selector choice)
# ---------------------------------------------------------------------------
SELECTOR_COMPARISON = {
    "plain_embedding_retriever_pct": 100.0,
    "agentic_llm_selector_pct": 75.6,
    "mis_routing_pct_embedding": 0.0,
}

# ---------------------------------------------------------------------------
# Part 2 -- run-time verification isolated (state-machine vs. flat script)
# ---------------------------------------------------------------------------
RUNTIME_VERIFICATION_ISOLATED = {
    "flat_script_mean": 10.6,
    "verified_state_machine_mean": 11.67,
    "delta": 0.67,
    "sign_test_p": 0.125,  # not significant -- paper is candid about this
}

# ---------------------------------------------------------------------------
# Part 2 -- out-of-distribution generalization (OSWorld corpus -> held-out)
# ---------------------------------------------------------------------------
OOD_GENERALIZATION = {
    "programs_in_corpus": 4,
    "held_out_tasks": 33,
    "held_out_domains": 9,
    "warm_ood_mean_pct": 55.6,
    "cold_baseline_pct": 67.0,  # unpaired n=1 baseline
}
