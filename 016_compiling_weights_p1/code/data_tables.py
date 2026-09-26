"""
data_tables.py -- every published number named in Part 1 and Part 2,
transcribed from backlog/011_compiling_workflows_into_weights.md (itself
cross-checked against "Compiling Agentic Workflows into LLM Weights",
arXiv:2605.22502) and both episodes' script.md.

Tagging convention:
  (paper, verified)  -- copied from a paper table, or a value directly
                        quoted in the backlog note and cross-checked
                        against the paper's own printed summary values.
  (paper, stated-delta) -- the paper states this delta directly; it may
                        not exactly equal subtracting the rounded table
                        cells above it (see README's rounding note).

Nothing in this file is invented.
"""

# ---------------------------------------------------------------------------
# The adoption puzzle that opens Part 1. (paper, verified)
# ---------------------------------------------------------------------------

ADOPTION_GAP = {
    "orchestration_frameworks_stars": 290_000,   # "290,000+ ... combined" (paper)
    "compilation_papers_stars": 3_000,           # "~3,000 stars combined" (paper)
    "paper_stated_ratio": "~100x less community engagement",  # (paper)
}

IN_CONTEXT_SELF_ORCHESTRATION_QUALITY_RANGE = (4.53, 5.00)  # companion paper, "near-perfect" (paper)

# ---------------------------------------------------------------------------
# Domain complexity, all three test procedures. (paper, verified)
# ---------------------------------------------------------------------------

DOMAINS = {
    "travel_booking": {"nodes": 14, "decision_hubs": 3, "unique_acyclic_paths": 86, "turns_range": (4, 17)},
    "zoom_support":   {"nodes": 14, "decision_hubs": None, "unique_acyclic_paths": 60, "turns_range": (4, 17)},
    "insurance_claims": {"nodes": 55, "decision_hubs": 6, "unique_acyclic_paths": 2381, "turns_range": (9, 39)},
}

# ---------------------------------------------------------------------------
# Table 1 -- Travel booking, 3B. Criterion: (3B Sub, 3B Orch, LG Orch, In-Context)
# (paper, verified)
# ---------------------------------------------------------------------------

TRAVEL_3B_TABLE = {
    "task_success":       {"sub_3b": 4.11, "orch_3b": 3.93, "langgraph": 4.17, "in_context": 4.53},
    "info_accuracy":      {"sub_3b": 4.75, "orch_3b": 4.69, "langgraph": 4.21, "in_context": 4.64},
    "consistency":        {"sub_3b": 4.34, "orch_3b": 4.12, "langgraph": 4.32, "in_context": 4.96},
    "graceful_handling":  {"sub_3b": 4.07, "orch_3b": 3.87, "langgraph": 4.62, "in_context": 4.96},
    "naturalness":        {"sub_3b": 4.12, "orch_3b": 3.96, "langgraph": 4.84, "in_context": 5.00},
}

# The same-model control (§4.1): 3B compiled vs. 3B orchestrated, SAME weights,
# SAME procedure. This is the causal core of Part 1. Deltas as stated by the
# paper (not recomputed from the rounded table above -- see README note).
SAME_MODEL_CONTROL = {
    "task_success":      {"delta": 0.18, "p": "<.001", "significant": True},
    "info_accuracy":     {"delta": 0.05, "p": ".29",   "significant": False},
    "consistency":       {"delta": 0.22, "p": "<.001", "significant": True},
    "graceful_handling": {"delta": 0.20, "p": "<.001", "significant": True},
    "naturalness":       {"delta": 0.17, "p": "<.001", "significant": True},
}  # (paper, stated-delta)

# ---------------------------------------------------------------------------
# Table 2 -- Zoom support, 8B. Criterion: (8B Sub, LG Orch, In-Context)
# (paper, verified)
# ---------------------------------------------------------------------------

ZOOM_8B_TABLE = {
    "task_success":       {"sub_8b": 4.50, "langgraph": 4.62, "in_context": 4.92},
    "info_accuracy":      {"sub_8b": 4.26, "langgraph": 4.75, "in_context": 4.92},
    "consistency":        {"sub_8b": 4.42, "langgraph": 4.55, "in_context": 5.00},
    "graceful_handling":  {"sub_8b": 4.62, "langgraph": 4.52, "in_context": 5.00},
    "naturalness":        {"sub_8b": 4.87, "langgraph": 4.64, "in_context": 5.00},
}

# ---------------------------------------------------------------------------
# Table 3 -- Insurance claims, 8B. Criterion: (In-Context, LG Orch, 8B Sub)
# (paper, verified)
# ---------------------------------------------------------------------------

INSURANCE_8B_TABLE = {
    "task_success":       {"in_context": 4.78, "langgraph": 4.42, "sub_8b": 4.47},
    "info_accuracy":      {"in_context": 4.78, "langgraph": 4.45, "sub_8b": 4.40},
    "consistency":        {"in_context": 4.82, "langgraph": 4.39, "sub_8b": 4.51},
    "graceful_handling":  {"in_context": 4.96, "langgraph": 4.38, "sub_8b": 4.81},
    "naturalness":        {"in_context": 5.00, "langgraph": 4.58, "sub_8b": 4.92},
}

# ---------------------------------------------------------------------------
# Failure rates (task success <= 3) and wall-clock/turns, Table 4-5 equivalents.
# (paper, verified)
# ---------------------------------------------------------------------------

FAILURE_RATES_PCT = {
    "travel_booking":   {"sub": 5.5,  "sub_n": (11, 200), "orch_same_model": 4.5, "orch_n": (9, 200), "langgraph": 24.0, "lg_n": (48, 200)},
    "zoom_support":      {"sub": 11.0, "sub_n": (22, 200), "langgraph": 9.0, "lg_n": (18, 200)},
    "insurance_claims":  {"sub": 9.0,  "sub_n": (18, 200), "langgraph": 17.0, "lg_n": (34, 200)},
}

WALLCLOCK_SECONDS = {
    "travel_booking":  {"sub": {"turns": 22.6, "seconds": 69.4}, "langgraph": {"turns": 16.5, "seconds": 64.9}, "in_context": {"turns": 16.4, "seconds": 55.5}},
    "zoom_support":     {"sub": {"turns": 13.6, "seconds": 29.5}, "langgraph": {"turns": 14.7, "seconds": 52.1}, "in_context": {"turns": 12.7, "seconds": 36.0}},
    "insurance_claims": {"sub": {"turns": 20.3, "seconds": 43.2}, "langgraph": {"turns": 26.4, "seconds": 120.8}, "in_context": {"turns": 19.0, "seconds": 52.8}},
}

INTERVIEW_STYLE_ONE_QUESTION_PCT = 64  # % of compiled model's turns with exactly one question (paper)
WORDS_PER_CONVERSATION_RANGE = (1200, 1400)  # comparable across conditions (paper)

# ---------------------------------------------------------------------------
# Cost. Table 6 (compound cost per conversation) + per-token cost inputs.
# (paper, verified)
# ---------------------------------------------------------------------------

COST_PER_CONVERSATION_TABLE = {
    # domain: {in_context, langgraph, subterranean, paper_stated_ic_over_sub_multiple}
    "travel_booking":   {"in_context": 0.133, "langgraph": 0.077, "subterranean": 0.0010, "paper_multiple": 128},
    "zoom_support":      {"in_context": 0.103, "langgraph": 0.054, "subterranean": 0.0003, "paper_multiple": 296},
    "insurance_claims":  {"in_context": 0.327, "langgraph": 0.174, "subterranean": 0.0007, "paper_multiple": 462},
}

LANGGRAPH_SPECIFIC_SAVINGS_RANGE = (77, 249)  # "77-249x cheaper than the LangGraph orchestrator" (paper)

PER_TOKEN_COST_INPUTS = {
    "a100_hourly_usd": 2.50,                 # reserved A100 80GB via vLLM (paper)
    "throughput_tokens_per_sec_range": (4000, 5000),  # (paper)
    "claude_input_per_million_usd": 3.0,     # Claude Sonnet 4.5 (paper)
    "claude_output_per_million_usd": 15.0,   # Claude Sonnet 4.5 (paper)
    "paper_stated_cheaper_multiple": 65,     # "roughly 65x cheaper per token" (paper)
}

PROMPT_TOKEN_OVERHEAD_MULTIPLE = {
    "travel_booking_14_nodes": 2,   # in-context re-serializes the flowchart every turn (paper)
    "insurance_claims_55_nodes": 7,  # (paper)
    "subterranean_prompt": 1,        # constant-size, one line (paper)
}

ONE_TIME_COMPILE_COST_USD = {
    "data_generation": 40,
    "finetune_compute_range": (10, 40),
    "total_range": (50, 80),
}  # (paper)

BREAKEVEN_CONVERSATIONS_STATED = 500          # "within 500 conversations on every domain" (paper)
MARGINAL_COST_PAST_10K_CONVOS_USD = 0.01      # "adds less than $0.01 per conversation" (paper)

# ---------------------------------------------------------------------------
# Recompile flexibility (§6). (paper, verified)
# ---------------------------------------------------------------------------

RECOMPILE_TIMELINE = {
    "data_generation_convos": 1600,
    "data_generation_minutes_concurrent": (15, 30),
    "data_generation_minutes_sequential": 60,
    "finetune_8xH200_minutes": (10, 15),
    "spotcheck_minutes_warm": 5,
    "spotcheck_minutes_cold": (10, 15),
    "fully_optimized_total_minutes": (30, 50),
    "single_a100_hours": (3, 4),
}

# ---------------------------------------------------------------------------
# The two honesty caveats Part 2 gives real weight to. (paper, verified)
# ---------------------------------------------------------------------------

INFO_ACCURACY_PLATEAU = {
    "at_8b_pct_of_in_context_zoom": 87,
    "at_8b_pct_of_in_context_insurance_range": (87, 92),
    "headline_spoken_figure_pct": 87,   # script SEG16: "stalls around eighty-seven percent"
    "reading": "broad world knowledge, not procedure following, is the bottleneck",
}

JUDGE_ROBUSTNESS = {
    "claude_judge_pct_of_in_context_range": (82, 102),
    "gpt41_judge_pct_of_in_context_range": (83, 99),
    "ranking_holds_under_both": "In-Context > LangGraph ~ Compiled > 3B Orchestrated",
    "caveat": "GPT-4.1 is harsher on the compiled model in some domains; the direction is robust, the exact percentage is judge-dependent",
}

# ---------------------------------------------------------------------------
# Data-provenance discrepancy this folder does not silently resolve.
# ---------------------------------------------------------------------------

ZOOM_TRAINING_CONVO_DISCREPANCY = {
    "convos_per_run": 870,
    "seeds": 8,
    "arithmetic_product": 870 * 8,     # = 6960
    "paper_stated_total": 6264,         # both numbers quoted directly from the backlog note
    "note": "870 x 8 = 6960, not 6264. Both figures are quoted directly from the source; "
            "this folder records both rather than picking one.",
}
