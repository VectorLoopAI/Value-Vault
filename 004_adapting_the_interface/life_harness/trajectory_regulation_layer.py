"""
Layer 4 — Trajectory Regulation Layer.

Fires AFTER feedback returns. Premise (paper Step 2, Layer 4; script SEG 19): many
agent failures are self-reinforcing -- the agent repeats an invalid command, loops
between equivalent states, or exhausts the budget without making progress -- and these
are detectable from trajectory-level PATTERNS (repetition, oscillation, no-progress),
not from deeper semantic understanding of the task. This layer tracks remaining budget
and escalates through four tiers: nothing -> soft recovery nudge -> repeated-failure
warning -> strong corrective directive.

Targets: TRAJECTORY_DEGENERATION failures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class RegulationResult:
    tier: str  # "none" | "soft_nudge" | "repeated_failure_warning" | "strong_directive"
    message: Optional[str]


class TrajectoryRegulationLayer:
    """Watches the running trajectory (actions + observations) and the remaining step
    budget, and produces a graduated, model-visible message when it detects
    repetition, oscillation, or stagnation. Cheap and purely pattern-based --
    deliberately does not require any model call of its own."""

    def __init__(
        self,
        step_budget: int,
        repetition_window: int = 3,
        oscillation_window: int = 4,
        stagnation_fraction: float = 0.5,
    ):
        self.step_budget = step_budget
        self.repetition_window = repetition_window
        self.oscillation_window = oscillation_window
        self.stagnation_fraction = stagnation_fraction
        self.action_history: List[Any] = []
        self.state_history: List[Any] = []
        self.progress_flags: List[bool] = []  # True if this step made measurable progress

    def record_step(self, action: Any, state_signature: Any, made_progress: bool) -> None:
        self.action_history.append(action)
        self.state_history.append(state_signature)
        self.progress_flags.append(made_progress)

    def _is_repeating(self) -> bool:
        w = self.repetition_window
        if len(self.action_history) < w:
            return False
        recent = self.action_history[-w:]
        return all(a == recent[0] for a in recent)

    def _is_oscillating(self) -> bool:
        w = self.oscillation_window
        if len(self.state_history) < w:
            return False
        recent = self.state_history[-w:]
        # A/B/A/B pattern (or longer even-length repeats of a 2-cycle).
        return len(set(recent)) <= 2 and recent[0] != recent[1] and recent[0::2] == [recent[0]] * (w // 2)

    def _is_stagnating(self, steps_taken: int) -> bool:
        if steps_taken == 0:
            return False
        no_progress_ratio = 1.0 - (sum(self.progress_flags) / steps_taken)
        budget_used_ratio = steps_taken / max(self.step_budget, 1)
        return no_progress_ratio >= self.stagnation_fraction and budget_used_ratio >= 0.5

    def regulate(self) -> RegulationResult:
        steps_taken = len(self.action_history)
        remaining_budget = self.step_budget - steps_taken
        repeating = self._is_repeating()
        oscillating = self._is_oscillating()
        stagnating = self._is_stagnating(steps_taken)

        if not (repeating or oscillating or stagnating):
            return RegulationResult(tier="none", message=None)

        budget_fraction_left = remaining_budget / max(self.step_budget, 1)

        if budget_fraction_left > 0.5:
            return RegulationResult(
                tier="soft_nudge",
                message=(
                    "You appear to be repeating a similar action without new progress. "
                    "Consider trying a different action or re-checking the current state "
                    "before continuing."
                ),
            )
        if budget_fraction_left > 0.2:
            return RegulationResult(
                tier="repeated_failure_warning",
                message=(
                    "Repeated-failure warning: the last several steps have not advanced "
                    "the task. This exact pattern has not worked -- do not repeat it. "
                    "Re-examine the goal and choose a materially different action."
                ),
            )
        return RegulationResult(
            tier="strong_directive",
            message=(
                f"Strong corrective directive: only {remaining_budget} steps remain and "
                "the trajectory has made no progress. Stop repeating prior actions. "
                "Re-read the task, check the current world state, and take the single "
                "most direct action toward the goal."
            ),
        )


if __name__ == "__main__":
    reg = TrajectoryRegulationLayer(step_budget=20)
    for i in range(6):
        reg.record_step(action="look", state_signature="room_1", made_progress=False)
    print(reg.regulate())
