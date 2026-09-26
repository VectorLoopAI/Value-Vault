"""
efc_score.py — Effective Feedback Compute (EFC): the four-gate event score.

Reference implementation of the mechanism from "Scaling Laws for Agent
Harnesses via Effective Feedback Compute" (Zhang, Wang, Xu, Zhu, Che —
Harbin Institute of Technology, 2026, arXiv:2605.29682v2), §3.2-3.3.

A feedback event only earns credit when it clears four gates
simultaneously — Informativeness (I), Validity (V), Non-redundant
relevance (R), Memory update (M), each bounded in [0, 1]. The event score
is the *product* of the four factors, scaled by a fixed constant kappa —
not a sum — so a single factor collapsing to zero zeroes the whole line
item. This is the "bottleneck by construction" design Part 1 of the video
calls "the ledger."
"""

from __future__ import annotations

from dataclasses import dataclass

KAPPA = 10.0  # kappa — fixed across every experiment in the paper (paper)


@dataclass(frozen=True)
class FeedbackEvent:
    """One row in the ledger. informativeness/validity/relevance/memory_update
    are each in [0, 1] — score them against concrete trace evidence, not
    vibes (§3.2: informativeness against a new constraint/reduced
    uncertainty/diagnosed failure/subgoal progress; validity against a
    deterministic checker/execution result/unit test/consistent tool
    observation)."""

    event_id: str
    informativeness: float  # I_t
    validity: float  # V_t
    relevance: float  # R_t — "non-redundant relevance"
    memory_update: float  # M_t

    def __post_init__(self):
        for name in ("informativeness", "validity", "relevance", "memory_update"):
            v = getattr(self, name)
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"{name}={v!r} must be in [0, 1] (event {self.event_id})")

    @property
    def score(self) -> float:
        """EFC_t = kappa * I_t * V_t * R_t * M_t (§3.2). Multiplicative, not
        additive: any single factor at 0 zeroes the event's credit — e.g. a
        perfect diagnosis that never reaches memory (M≈0) contributes
        almost nothing, regardless of how informative or valid it was."""
        return KAPPA * self.informativeness * self.validity * self.relevance * self.memory_update


def run_efc(events: list[FeedbackEvent]) -> float:
    """EFC(tau) = sum_t EFC_t — run-level score is just the ledger total."""
    return sum(e.score for e in events)


if __name__ == "__main__":
    # The two contrasting examples from Part 1 (SEG 05-07): a perfect
    # diagnosis that never reaches memory, vs. a verified fix that does.
    diagnosed_but_lost = FeedbackEvent(
        "bug_diagnosis_never_stored", informativeness=0.9, validity=0.95, relevance=0.9, memory_update=0.02
    )
    retained_fix = FeedbackEvent(
        "verified_fix_stored_in_memory", informativeness=0.8, validity=1.0, relevance=0.85, memory_update=0.9
    )
    repeated_stack_trace = FeedbackEvent(
        "retry_same_failing_command", informativeness=0.1, validity=0.9, relevance=0.05, memory_update=0.1
    )
    ledger = [diagnosed_but_lost, retained_fix, repeated_stack_trace]
    for e in ledger:
        print(
            f"{e.event_id:32s} I={e.informativeness:.2f} V={e.validity:.2f} "
            f"R={e.relevance:.2f} M={e.memory_update:.2f} -> EFC_t={e.score:.3f}"
        )
    print(f"run-level EFC(tau) = {run_efc(ledger):.3f}")
