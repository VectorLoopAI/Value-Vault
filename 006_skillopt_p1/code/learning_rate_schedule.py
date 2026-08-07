"""
learning_rate_schedule.py — the textual learning rate L_t from SkillOpt §3.4.

L_t is the maximum number of skill edits the optimizer is allowed to apply
at step t. Paper default: L_t starts at 4 and decays to a floor of 2 across
4 epochs under a cosine schedule; constant and linear schedules are also
supported in the paper's ablation sweep (§4.2).
"""

from __future__ import annotations

import math


def textual_learning_rate(
    epoch: int,
    total_epochs: int = 4,
    lt_start: int = 4,
    lt_floor: int = 2,
    schedule: str = "cosine",
) -> int:
    """Return L_t (an integer edit budget) for the given epoch (0-indexed).

    schedule: "constant" | "linear" | "cosine" (paper default).
    "autonomous" (an optimizer-decided budget) is named in the paper but not
    specified numerically, so it is not reproduced here — pick one of the
    three fixed schedules above for a runnable default.
    """
    if total_epochs <= 1:
        return lt_start

    progress = epoch / (total_epochs - 1)  # 0.0 .. 1.0
    progress = min(max(progress, 0.0), 1.0)

    if schedule == "constant":
        value = lt_start
    elif schedule == "linear":
        value = lt_start - progress * (lt_start - lt_floor)
    elif schedule == "cosine":
        cos_term = (1 + math.cos(math.pi * progress)) / 2  # 1 -> 0
        value = lt_floor + cos_term * (lt_start - lt_floor)
    else:
        raise ValueError(f"unknown schedule: {schedule!r}")

    return max(lt_floor, round(value))


def clip_to_budget(ranked_edits: list, lt: int) -> list:
    """Clip a utility-ranked edit pool (best first) to the top L_t entries —
    §3.4: "the pool gets ranked ... then clipped to the top L_t."
    """
    return ranked_edits[:lt]


if __name__ == "__main__":
    for schedule in ("constant", "linear", "cosine"):
        values = [textual_learning_rate(e, total_epochs=4, schedule=schedule) for e in range(4)]
        print(f"{schedule:>9}: {values}")
