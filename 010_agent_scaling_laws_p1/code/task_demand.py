"""
task_demand.py — D_task, the normalization that turns EFC into a
task-relative coordinate (§3.4). Two tasks can need very different amounts
of feedback to be "done" — D_task makes that scale explicit so EFC/D_task
compares fairly across tasks of different difficulty. More available
verification only *lowers* D_task (never raises it) — a well-covered task
needs less feedback to reach a given confidence.
"""

from __future__ import annotations

from dataclasses import dataclass

EPSILON_D = 0.001  # floor keeping D_task off zero for trivial tasks (illustrative — paper states a floor exists, not its exact number)


@dataclass(frozen=True)
class TaskDemandFactors:
    min_steps: float  # L — minimum reasoning/action steps
    tool_ambiguity: float  # H_tool — tool-selection ambiguity
    state_pressure: float  # S_state — state-tracking demand
    obs_noise: float  # N_obs — observation noise
    verifier_visibility: float  # V_ver in [0, 1] — coverage by reliable checks

    @property
    def d_task(self) -> float:
        """D_task = max(eps_D, L * H_tool * S_state * (1+N_obs) * (1 - V_ver))"""
        raw = (
            self.min_steps
            * self.tool_ambiguity
            * self.state_pressure
            * (1.0 + self.obs_noise)
            * (1.0 - self.verifier_visibility)
        )
        return max(EPSILON_D, raw)


def normalize(efc_value: float, demand: TaskDemandFactors) -> float:
    """X = EFC / D_task — feedback per unit of what the task actually
    requires. This is the normalization behind the paper's headline
    Oracle-EFC/D_task result (Part 1: R² = 0.99)."""
    return efc_value / demand.d_task


if __name__ == "__main__":
    well_covered_task = TaskDemandFactors(
        min_steps=4, tool_ambiguity=1.1, state_pressure=1.0, obs_noise=0.1, verifier_visibility=0.8
    )
    poorly_covered_task = TaskDemandFactors(
        min_steps=4, tool_ambiguity=1.1, state_pressure=1.0, obs_noise=0.1, verifier_visibility=0.1
    )
    efc_value = 6.4
    print(f"well-covered task   D_task={well_covered_task.d_task:.3f}  X={normalize(efc_value, well_covered_task):.3f}")
    print(f"poorly-covered task D_task={poorly_covered_task.d_task:.3f}  X={normalize(efc_value, poorly_covered_task):.3f}")
