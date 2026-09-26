"""
demo.py — end-to-end toy loop over one AdaCoM manager decision, showing the
edit schema, the three rule-based process rewards, and the two-level
advantage estimator working together on a tiny synthetic group of 2
rollouts. Zero external dependencies — Python 3.10+ stdlib only.

Run: python3 demo.py
"""

from __future__ import annotations

from context_ops import Message, Operation, apply_operations, needs_forced_extract
from process_rewards import (
    ToolCall,
    token_penalty,
    redundant_action_penalty,
    format_penalty,
    gold_doc_found_bonus,
)
from advantage import combine_advantages


def demo_context_edit() -> None:
    print("=== 1. Applying a manager action to a pre-management context ===")
    context = [
        Message(id=1, role="user", content="Task: find the founding year of the paper's lead lab."),
        Message(id=2, role="assistant", content="search('Renmin University Tongyi Lab founding')"),
        Message(id=3, role="user", content="[tool result: 40 lines of raw search snippets...]"),
        Message(id=4, role="assistant", content="search('Renmin University Tongyi Lab founding')"),
        Message(id=5, role="user", content="[tool result: same 40 lines again, redundant call]"),
    ]

    operations = [
        # Merge the first search+result pair (ids 2-3) into a condensed
        # working note -- new_content non-empty -> rewrite/merge.
        Operation(
            ids=[2, 3],
            role="ASSISTANT",
            justification="condense first search + raw result into a working note",
            new_content="Working note: searched lab founding info; no confirmed year yet.",
        ),
        # Delete the second, redundant search+result pair (ids 4-5) outright
        # -- new_content empty -> delete.
        Operation(
            ids=[4, 5],
            role="ASSISTANT",
            justification="second search was redundant with the first -- delete outright",
            new_content="",
        ),
    ]

    managed = apply_operations(context, operations)
    for m in managed:
        print(f"  id={m.id} role={m.role:9s} content={m.content[:60]!r}")

    print(f"\n  needs_forced_extract('get_article')      = {needs_forced_extract('get_article')}")
    print(f"  needs_forced_extract('search_wikipedia')  = {needs_forced_extract('search_wikipedia')}\n")


def demo_process_rewards() -> None:
    print("=== 2. Rule-based process rewards for one manager step ===")
    prev_call = ToolCall(name="search", params={"query": "lab founding year"})
    repeated_call = ToolCall(name="search", params={"query": "lab founding year"})

    tp = token_penalty(managed_context_tokens=33500, length_limit=32768)
    rap = redundant_action_penalty(repeated_call, prev_call)
    fp = format_penalty(
        '[{"ids": [2], "role": "ASSISTANT", "justification": "ok"}]',
        context_ids={1, 2, 3, 4, 5},
    )
    gb = gold_doc_found_bonus(gold_document_found=True)

    print(f"  token_penalty (over limit)      = {tp}")
    print(f"  redundant_action_penalty (dupe) = {rap}")
    print(f"  format_penalty (missing field)  = {fp}   # new_content is missing -> caught")
    print(f"  gold_doc_found_bonus            = {gb}\n")


def demo_advantage() -> None:
    print("=== 3. Two-level advantage over a toy group of 2 rollouts ===")
    # Both rollouts happen to earn the SAME outcome reward -- this is the
    # case the paper calls out: sigma_R = 0, so the task-level term
    # vanishes and the step-level (process-reward) term is the only signal.
    outcome_rewards = [1.0, 1.0]
    process_rewards_per_rollout = [
        [0.0, -1.0, 1.0],   # rollout A: a redundant-action penalty, then a gold-doc bonus
        [0.0, 0.0, 0.0],    # rollout B: clean run, no rule fired
    ]

    combined = combine_advantages(outcome_rewards, process_rewards_per_rollout, alpha=0.1)
    for i, steps in enumerate(combined):
        print(f"  rollout {i}: {[round(a, 4) for a in steps]}")
    print("\n  Same outcome reward on both rollouts -> task-level term ~0 for both;")
    print("  the spread you see above is coming entirely from the step-level term.\n")


if __name__ == "__main__":
    demo_context_edit()
    demo_process_rewards()
    demo_advantage()
