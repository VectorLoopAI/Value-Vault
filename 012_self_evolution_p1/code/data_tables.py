"""
data_tables.py -- every published number named in Part 1 and Part 2,
transcribed from backlog/009_disentangling_self_evolution.md (itself
cross-checked against the paper's tables) and both episodes' script.md.

Tagging convention:
  (paper, verified)  -- copied from a paper table, or a reconstruction the
                        backlog note independently re-derived and confirmed
                        against the paper's own printed summary values.
  (paper, partial)   -- the paper states a stronger global fact (e.g. "at
                        most 3.1 pp across all seven evolvers on any
                        benchmark") than the specific named cells below;
                        only the cells actually named on-camera are
                        recorded here, not the full 7x3 grid. Never
                        interpolated or guessed.

Nothing in this file is invented.
"""

# ---------------------------------------------------------------------------
# PART 1 -- harness-updating (the writer). Delta_update per evolver, per
# benchmark, for the specific evolvers named in Part 1 / the backlog note.
# (paper, partial) -- see module docstring.
# ---------------------------------------------------------------------------

EVOLVER_UPDATING_PARTIAL = {
    "SWE": {
        "Qwen3-235B-A22B": 8.2,   # best on SWE (paper, verified)
        "GPT-OSS-120B": 5.9,      # worst on SWE (paper, verified)
    },
    "MCP": {
        "Claude Opus 4.6": 3.6,   # best on MCP (paper, verified)
        "Qwen3-235B-A22B": 0.6,   # worst on MCP -- same model that led SWE (paper, verified)
    },
    "SB": {
        "Qwen3.5-9B": 3.8,        # best on SB -- the smallest model in the study (paper, verified)
        "Claude Opus 4.6": 2.3,   # (paper, verified)
        "Qwen3-235B-A22B": 1.5,   # (paper, verified)
        "Claude Sonnet 4.6": 1.2, # worst on SB (paper, verified)
    },
}

EVOLVER_GLOBAL_SPREAD_CLAIM_PP = 3.1   # paper's own headline: max spread across ALL 7 evolvers, any benchmark

FLINK_QUERY_CASE_STUDY = {
    # SkillsBench task, solver pinned to Claude Opus 4.6 in all three conditions
    "no_skill": 0.67,
    "skill_by_qwen3_5_9b": 1.0,
    "skill_by_opus_4_6": 1.0,
    "procedure_steps": [
        "filter SUBMIT events",
        "filter FINISH events",
        "count each SUBMIT separately",
        "emit (jobId, count)",
        "apply a 10-minute session window",
    ],
    "divergence": "manual batch sessionization (Qwen3.5-9B) vs. KeyedProcessFunction (Opus 4.6) -- plumbing only",
}

# ---------------------------------------------------------------------------
# PART 2 -- harness-benefit (the reader). Table 1, in full: six agents,
# three benchmarks, (base_capability_pct, delta_benefit_pp). (paper, verified)
# ---------------------------------------------------------------------------

AGENT_BENEFIT_TABLE = {
    "Qwen3-32B":       {"SWE": (3.6, 4.4),  "MCP": (3.6, 1.0),  "SB": (0.0, 5.8)},
    "Qwen3-235B-A22B": {"SWE": (20.7, 19.3), "MCP": (25.0, 4.3), "SB": (4.7, 1.1)},
    "GPT-OSS-120B":    {"SWE": (26.2, 15.8), "MCP": (28.0, 7.0), "SB": (0.0, 7.0)},
    "Haiku 4.5":       {"SWE": (66.0, 2.4),  "MCP": (42.4, 3.6), "SB": (5.8, 15.1)},
    "Sonnet 4.6":      {"SWE": (73.2, 2.8),  "MCP": (54.0, 3.2), "SB": (24.4, 3.5)},
    "Opus 4.6":        {"SWE": (74.2, 2.6),  "MCP": (61.0, 3.6), "SB": (25.6, 5.8)},
}

# ---------------------------------------------------------------------------
# PART 2 -- activation vs. adherence, SkillsBench, all six agent-side models.
# SLR = skill-load rate, HFR = harness-following rate,
# LPR = pass-when-loaded rate. (paper, verified)
# ---------------------------------------------------------------------------

ACTIVATION_ADHERENCE_TABLE = {
    "Qwen3-32B":       {"SLR": 0.251, "HFR": 0.142, "LPR": 0.023},
    "GPT-OSS-120B":    {"SLR": 0.446, "HFR": 0.442, "LPR": 0.040},
    "Haiku 4.5":       {"SLR": 0.794, "HFR": 0.600, "LPR": 0.099},
    "Qwen3-235B-A22B": {"SLR": 0.961, "HFR": 0.350, "LPR": 0.022},
    "Sonnet 4.6":      {"SLR": 0.959, "HFR": 0.730, "LPR": 0.145},
    "Opus 4.6":        {"SLR": 0.957, "HFR": 0.757, "LPR": 0.177},
}

# ---------------------------------------------------------------------------
# PART 2 -- phase-level adherence drift for three representative models
# (weak / mid / strong), scored at three trajectory phases. (paper, verified)
# ---------------------------------------------------------------------------

ADHERENCE_DRIFT_TABLE = {
    "Qwen3-32B (weak)":    [0.52, 0.22, 0.13],
    "GPT-OSS-120B (mid)":  [0.67, 0.48, 0.43],
    "Opus 4.6 (strong)":   [0.89, 0.79, 0.80],
}
DRIFT_PHASE_LABELS = ["harness loaded", "mid turn", "final turn"]

# ---------------------------------------------------------------------------
# PART 2 -- extreme-pairing stress test: weakest anchor agent + its best
# evolver vs. strongest anchor agent + its worst evolver. Margin the strong
# side still wins by, per benchmark. (paper, verified)
# ---------------------------------------------------------------------------

EXTREME_PAIRING_MARGIN_PP = {
    "SWE": 35.2,
    "MCP": 32.3,
    "SB": 18.6,
}

# ---------------------------------------------------------------------------
# The SkillsBench honesty caveat, named explicitly in both episodes.
# ---------------------------------------------------------------------------

SKILLSBENCH_CAVEAT = (
    "SWE-bench and MCP-Atlas give the clearest evidence for both the evolver-"
    "flatness result and the non-monotonic harness-benefit curve. SkillsBench's "
    "low-base regime is more variable across task domains (the paper's own words): "
    "its evolver-side headline is Qwen3.5-9B beating Opus 4.6 (3.8 pp vs 2.3 pp), "
    "and its agent-side benefit table has Haiku 4.5 (a strong-tier closed model) "
    "posting the largest gain at 15.1 pp, with Qwen3-32B tying Opus 4.6 exactly at "
    "5.8 pp -- the opposite of the mid-tier-peaks story that holds on SWE and MCP."
)
