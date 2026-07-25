#!/usr/bin/env python3
"""
P1 — Hierarchical Delegation (Coordination concern).

One orchestrator owns the outcome, dispatches sub-tasks to specialist sub-agents, and merges
their outputs. The design rule from the video (SEG 13), the tweetable one:

    "The LLM proposes, deterministic code decides."

The merge step MUST be plain deterministic code, never another LLM call. If you let an LLM merge,
it develops a *preference* and one sub-agent's output starts dominating beyond its declared
weight -- that's the exact P1 failure signature from SEG 26's catalog. The retry budget also
belongs to the parent, not the children -- double retries (parent AND child both retrying the
same failure) is the other named P1 failure mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass
class SubAgentResult:
    agent_name: str
    field: str
    value: float
    weight: float  # declared weight/confidence -- the merge must respect this, an LLM merge won't


class SubAgentStalledError(Exception):
    pass


class HierarchicalOrchestrator:
    """P1: dispatch to specialists, merge deterministically, own the retry budget."""

    def __init__(self, retry_budget: int = 2):
        self.retry_budget = retry_budget  # owned by the PARENT -- children must not retry themselves
        self._audit: List[str] = []

    def dispatch(
        self,
        sub_agents: Dict[str, Callable[[], SubAgentResult]],
    ) -> List[SubAgentResult]:
        """Run each sub-agent once per call; the parent, not the sub-agent, decides on retries."""
        results = []
        for name, run in sub_agents.items():
            attempts = 0
            result: Optional[SubAgentResult] = None
            while attempts <= self.retry_budget:
                try:
                    result = run()
                    break
                except SubAgentStalledError:
                    attempts += 1
                    self._audit.append(f"retry {attempts}/{self.retry_budget} for sub-agent '{name}'")
            if result is None:
                self._audit.append(f"sub-agent '{name}' stalled after {self.retry_budget} retries")
                continue
            results.append(result)
        return results

    @staticmethod
    def deterministic_merge(results: List[SubAgentResult]) -> Dict[str, float]:
        """Plain, auditable code -- weighted average per field. No LLM in this step, ever.

        This is what stops any single sub-agent's output from dominating beyond its declared
        weight, which is exactly the failure mode an LLM-based merge introduces (SEG 13/26).
        """
        by_field: Dict[str, List[SubAgentResult]] = {}
        for r in results:
            by_field.setdefault(r.field, []).append(r)

        merged: Dict[str, float] = {}
        for field_name, rs in by_field.items():
            total_weight = sum(r.weight for r in rs)
            if total_weight == 0:
                merged[field_name] = sum(r.value for r in rs) / len(rs)
            else:
                merged[field_name] = sum(r.value * r.weight for r in rs) / total_weight
        return merged

    @property
    def audit_log(self) -> List[str]:
        return list(self._audit)


if __name__ == "__main__":
    orchestrator = HierarchicalOrchestrator(retry_budget=1)

    def churn_scoring_agent() -> SubAgentResult:
        return SubAgentResult(agent_name="churn_scoring", field="risk_score", value=0.72, weight=0.6)

    def offer_drafting_agent() -> SubAgentResult:
        return SubAgentResult(agent_name="offer_drafting", field="risk_score", value=0.55, weight=0.4)

    results = orchestrator.dispatch({
        "churn_scoring": churn_scoring_agent,
        "offer_drafting": offer_drafting_agent,
    })
    merged = orchestrator.deterministic_merge(results)
    print(f"merged (deterministic code, not an LLM): {merged}")
    for line in orchestrator.audit_log:
        print(line)
