"""
demo.py — a runnable, miniature version of the SkillOpt loop tying together
learning_rate_schedule.py, skill_patch.py, and gate.py.

This is a toy two-epoch run over a spreadsheet-style task (echoing the
paper's SpreadsheetBench case study, §4.5), not a reproduction of the
paper's actual training data or scores. It exists to make the mechanism
runnable and inspectable, not to reproduce a benchmark number.
"""

from __future__ import annotations

import json

from gate import ValidationGate
from learning_rate_schedule import clip_to_budget, textual_learning_rate
from skill_patch import SkillDocument


def rank_by_utility(candidate_edits: list[dict]) -> list[dict]:
    """Stand-in for the paper's Ranking.md contract (systematic impact,
    complementarity, generality, actionability). Here we just sort by the
    mock `support_count` and `utility` fields each edit already carries —
    a real optimizer call would produce these from Merge_Final.md's output.
    """
    return sorted(candidate_edits, key=lambda e: (e["support_count"], e["utility"]), reverse=True)


def run_demo() -> None:
    skill = SkillDocument.from_lines(["Inspect workbook structure and formulas before answering."])

    # SEG19's case study: SpreadsheetBench starts at 40.4.
    gate = ValidationGate(current_skill=skill, current_score=0.404)

    # A mocked pool of candidate edits the optimizer proposed after each
    # rollout batch, carrying the merge stage's support_count and a rough
    # utility score (see prompts/ranking.md for the real contract).
    epoch_edits = [
        [
            {
                "op": "append",
                "text": "Write evaluated static values instead of leaving formulas for the grader to recalculate.",
                "support_count": 14,
                "utility": 0.91,
            },
            {
                "op": "append",
                "text": "Double-check currency formatting matches the source locale.",
                "support_count": 2,
                "utility": 0.35,
            },
        ],
        [
            {
                "op": "insert_after",
                "target_id": "R1",
                "text": "If a cell references another sheet, resolve the reference before writing the value.",
                "support_count": 9,
                "utility": 0.78,
            },
        ],
    ]

    # Mock selection-split scores the gate would compute by re-running the
    # candidate skill through the harness — hardcoded here for a runnable
    # demo. Epoch 1's edit makes the score worse: SEG14's "plausible,
    # well-reasoned rule that hurts the actual target model" scenario.
    mock_selection_scores = [0.789, 0.760]

    reports = []
    for epoch, (edits, mock_score) in enumerate(zip(epoch_edits, mock_selection_scores)):
        lt = textual_learning_rate(epoch, total_epochs=len(epoch_edits))
        ranked = rank_by_utility(edits)
        clipped = clip_to_budget(ranked, lt)

        candidate = gate.current_skill.clone()
        candidate.apply(clipped)

        report = gate.evaluate(candidate, mock_score, clipped, epoch)
        report["epoch"] = epoch
        report["textual_learning_rate"] = lt
        reports.append(report)

    print("edit_apply_report (per epoch):")
    print(json.dumps(reports, indent=2))

    print("\nfinal best_skill.md:")
    print(gate.best_skill.to_markdown())
    print(f"\nestimated tokens: {gate.best_skill.token_estimate()}")

    rejected = gate.clear_epoch_buffer()
    if rejected:
        print("\nrejected-edit buffer (fed into the next reflection call, §3.5):")
        for r in rejected:
            print(f"  epoch {r.epoch}: score dropped by {r.score_drop:.3f} — edits: {r.edits}")


if __name__ == "__main__":
    run_demo()
