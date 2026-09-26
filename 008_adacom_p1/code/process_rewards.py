"""
process_rewards.py — the three rule-based process rewards from AdaCoM
§3.2.

No extra LLM judge, no learned reward model — three computable rules that
supplement the sparse trajectory-level outcome reward (the task-solving
agent's final-answer score). Ablating these costs DeepSeek-V3 1.81 points
and Qwen3-Max 3.34 points of mean@3 on BrowseComp-Plus (paper, Table 5).

Penalty/bonus magnitudes below are (illustrative) — the paper names and
motivates each rule exactly, but does not publish the numeric scale of any
of them; calibrate against your own judge/environment in a real setup.
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    params: dict


def token_penalty(managed_context_tokens: int, length_limit: int, magnitude: float = -1.0) -> float:
    """Charged to the manager step whose edit left the managed context
    over the length limit (paper)."""
    return magnitude if managed_context_tokens > length_limit else 0.0


def redundant_action_penalty(action_t: ToolCall, action_t_minus_1, magnitude: float = -1.0) -> float:
    """Fires when the agent issues two consecutive identical tool calls —
    same name, same parameters. Treated as a proxy for the manager having
    failed to preserve information the agent needed to avoid repeating
    itself (paper)."""
    if action_t_minus_1 is None:
        return 0.0
    same = action_t.name == action_t_minus_1.name and action_t.params == action_t_minus_1.params
    return magnitude if same else 0.0


def format_penalty(raw_manager_output: str, context_ids: set, magnitude: float = -1.0) -> float:
    """Fires on invalid manager JSON, nonexistent message ids, or missing
    required fields (paper). Returns the penalty (0.0 if the output is
    well-formed) — this is the reward-side wrapper around the same schema
    check `context_ops.validate_operations` performs on parsed operations."""
    try:
        ops = json.loads(raw_manager_output)
    except json.JSONDecodeError:
        return magnitude

    if not isinstance(ops, list):
        return magnitude

    required = {"ids", "role", "justification", "new_content"}
    for op in ops:
        if not isinstance(op, dict) or not required.issubset(op.keys()):
            return magnitude
        if not set(op["ids"]).issubset(context_ids):
            return magnitude
    return 0.0


def gold_doc_found_bonus(gold_document_found: bool, magnitude: float = 1.0) -> float:
    """BrowseComp-Plus only: a positive process reward when a search step
    surfaces a gold/key document, credited to the manager step that
    preceded that search (paper)."""
    return magnitude if gold_document_found else 0.0
