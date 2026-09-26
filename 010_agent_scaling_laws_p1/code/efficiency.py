"""
efficiency.py — the two orthogonal quality metrics the paper decomposes
harness quality into (§3.4, §5; Part 2 SEG 07-08):

  eta = EFC / C_raw   — harness efficiency: how well the harness converts
                         raw budget into effective feedback
  X   = EFC / D_task   — task-normalized feedback: whether that feedback
                         is enough for what the task needs

They answer different questions when a run fails: eta answers "is my
harness converting budget into useful feedback" (a conversion problem —
fix routing/verification/memory); X answers "is there enough feedback for
what this task demands" (a sufficiency problem — the task itself may be
past what any harness of this kind can solve at this budget). Router
quality gives the largest efficiency gain (+0.28 in the paper's module
ablation); observation noise gives the largest tax (-0.17).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HarnessDiagnosis:
    run_id: str
    efc: float
    raw_cost: float
    d_task: float

    @property
    def eta(self) -> float:
        """Harness efficiency — EFC/C_raw."""
        return self.efc / max(self.raw_cost, 1e-9)

    @property
    def task_normalized_feedback(self) -> float:
        """X = EFC/D_task."""
        return self.efc / max(self.d_task, 1e-9)

    def diagnose(self, eta_floor: float, x_floor: float) -> str:
        """Toy diagnostic rule mirroring the video's framing (Part 2
        SEG 07): low eta -> conversion problem (routing/verification/
        memory); low X (with eta healthy) -> sufficiency problem (task
        demand too high for this harness at this budget)."""
        if self.eta < eta_floor:
            return "conversion problem: harness is not converting budget into useful feedback (fix routing/verification/memory)"
        if self.task_normalized_feedback < x_floor:
            return "sufficiency problem: not enough feedback for what this task demands, even though conversion is healthy"
        return "healthy: conversion and sufficiency both clear their floors"


if __name__ == "__main__":
    weak_routing_run = HarnessDiagnosis("weak_routing", efc=1.2, raw_cost=45.0, d_task=2.0)
    healthy_run = HarnessDiagnosis("healthy", efc=18.0, raw_cost=45.0, d_task=2.0)
    for run in (weak_routing_run, healthy_run):
        print(
            f"{run.run_id:14s} eta={run.eta:.3f} X={run.task_normalized_feedback:.3f} "
            f"-> {run.diagnose(eta_floor=0.15, x_floor=5.0)}"
        )
