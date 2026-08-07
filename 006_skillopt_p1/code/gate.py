"""
gate.py — the held-out validation gate + rejected-edit buffer from SkillOpt
§3.5.

Reference implementation of the mechanism described in the SkillOpt paper
(arXiv:2605.23904v2, Microsoft / SJTU / Tongji / Fudan): every candidate
skill is scored on the disjoint selection split D_sel, and is accepted only
when its score is *strictly* greater than the current selection score —
ties are rejected outright, so the deployed skill never silently drifts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RejectedStep:
    epoch: int
    edits: list
    proposed_score: float
    current_score: float

    @property
    def score_drop(self) -> float:
        return self.current_score - self.proposed_score


@dataclass
class ValidationGate:
    """Implements the strict accept/reject rule from §3.5.

    current_skill / current_score track the *chain* the optimizer is
    currently editing forward from. best_skill / best_score track the file
    that actually ships (`best_skill.md`) — these only move together when a
    candidate both improves the chain *and* sets a new all-time high.
    """

    current_skill: Any
    current_score: float
    best_skill: Any = None
    best_score: float = float("-inf")
    epoch_buffer: list = field(default_factory=list)

    def __post_init__(self):
        if self.best_skill is None:
            self.best_skill = self.current_skill
            self.best_score = self.current_score

    def evaluate(self, candidate_skill: Any, candidate_score: float, edits: list, epoch: int) -> dict:
        """Score a candidate on the selection split and apply the gate.

        Returns an `edit_apply_report`-style dict: the shape §3.5 says gets
        written to disk every step — `{"accepted": bool, "new_best": bool,
        "edits": [...], "current_score": ..., "candidate_score": ...}`.
        """
        accepted = candidate_score > self.current_score  # strict — ties rejected
        new_best = accepted and candidate_score > self.best_score

        if accepted:
            self.current_skill = candidate_skill
            self.current_score = candidate_score
            if new_best:
                self.best_skill = candidate_skill
                self.best_score = candidate_score
        else:
            self.epoch_buffer.append(
                RejectedStep(
                    epoch=epoch,
                    edits=edits,
                    proposed_score=candidate_score,
                    current_score=self.current_score,
                )
            )

        return {
            "accepted": accepted,
            "new_best": new_best,
            "edits": edits,
            "current_score": self.current_score,
            "candidate_score": candidate_score,
        }

    def clear_epoch_buffer(self) -> list:
        """Called at epoch boundaries once the buffer has been folded into
        the next reflection call (§3.5: "feeds into later reflection calls
        in the same epoch").
        """
        buf, self.epoch_buffer = self.epoch_buffer, []
        return buf
