"""
context_ops.py — the AdaCoM manager action space (paper §3.1).

Reference implementation of the four-field edit operation described in
"Learning Agent-Compatible Context Management For Long-Horizon Tasks"
(arXiv:2605.30785v1, Renmin University of China / Tongyi Lab, Alibaba
Group / BUPT / Universite de Montreal). Every message in a context has a
unique id; the manager emits a list of operations, each targeting a
consecutive run of ids. Empty new_content deletes; non-empty
rewrites/merges; anything untouched is copied through unchanged; an empty
operation list leaves the context exactly as it was.

New-message id assignment (see `next_id` handling below) is an
implementation detail the paper doesn't specify exactly — (illustrative),
not (paper).
"""

from __future__ import annotations

from dataclasses import dataclass


VALID_ROLES = {"SYSTEM", "USER", "ASSISTANT"}


@dataclass
class Message:
    id: int
    role: str      # "system" | "user" | "assistant"
    content: str


@dataclass
class Operation:
    ids: list          # list[int] — consecutive message ids this op targets (paper)
    role: str          # SYSTEM | USER | ASSISTANT (paper)
    justification: str  # private rationale, stripped before the agent sees it (paper)
    new_content: str    # "" -> delete; non-empty -> rewrite/merge (paper)


class InvalidOperation(ValueError):
    """Raised for anything the paper's format_penalty rule would catch:
    malformed structure upstream of this function, nonexistent message
    ids, missing fields, or overlapping operations."""


def validate_operations(context: list, operations: list) -> None:
    context_ids = {m.id for m in context}
    seen: set = set()
    for op in operations:
        if op.role not in VALID_ROLES:
            raise InvalidOperation(f"invalid role {op.role!r}")
        if not op.ids:
            raise InvalidOperation("operation.ids must be non-empty")
        sorted_ids = sorted(op.ids)
        if sorted_ids != list(range(sorted_ids[0], sorted_ids[0] + len(sorted_ids))):
            raise InvalidOperation(f"ids {op.ids} are not consecutive")
        missing = set(op.ids) - context_ids
        if missing:
            raise InvalidOperation(f"ids {sorted(missing)} do not exist in context")
        overlap = seen & set(op.ids)
        if overlap:
            raise InvalidOperation(f"ids {sorted(overlap)} targeted by more than one operation")
        seen |= set(op.ids)


def apply_operations(context: list, operations: list) -> list:
    """Apply a manager action to a pre-management context (paper §3.1:
    c_t -> managed context c~_t).

    An empty `operations` list returns the context unchanged.
    """
    validate_operations(context, operations)

    op_by_start = {min(op.ids): op for op in operations}
    covered_ids = {i for op in operations for i in op.ids}
    next_id = (max((m.id for m in context), default=0)) + 1

    result: list = []
    for msg in context:
        if msg.id not in covered_ids:
            result.append(msg)
            continue
        op = op_by_start.get(msg.id)
        if op is None:
            continue  # interior/tail id of a multi-message merge — already handled at its start id
        if op.new_content == "":
            continue  # empty new_content deletes the targeted messages (paper)
        result.append(Message(id=next_id, role=op.role.lower(), content=op.new_content))
        next_id += 1
    return result


# --- MCP-Bench-Wiki's one fixed exception (paper §3.1 note) -----------------

WIKIPEDIA_MCP_TOOLS = [
    "search_wikipedia", "get_article", "get_summary",
    "summarize_article_for_query", "summarize_article_section",
    "extract_key_facts", "get_related_topics", "get_sections", "get_links",
]

EXTRACT_TRIGGER_TOOL = "get_article"


def needs_forced_extract(tool_name: str) -> bool:
    """True whenever a `get_article` result lands — AdaCoM always runs an
    `extract` operation before the next agent step in that case,
    regardless of what the manager's learned policy would otherwise choose
    (paper), to prevent unbounded growth from full Wikipedia articles."""
    return tool_name == EXTRACT_TRIGGER_TOOL
