"""
efc_adapter.py — EFC-ADAPTER: the ROI-scored control layer from §7 / Part
2 (SEG 15-17). Bolts onto an *existing* harness — same model, task
interface, tool set, action space, raw-budget cap — and makes four
decisions off the ledger: score candidate actions by ROI, retain verified
feedback into durable memory, gate self-evolution updates, and stop or
roll back once ROI saturates.

ROI(a_t) = E[delta NRS-EFC(a_t)/D_task_hat | prefix] / E[delta C_raw(a_t) | prefix]

Uses only prefix-visible information — no future events, no hidden
solution, no final success label wired in anywhere below. Attached to
four existing methods in the paper (mini-SWE-agent, AHE, RTV, PDR) it
lifts mean pass rate 61.2% -> 68.2% while cutting mean raw cost
213.8 -> 85.1, without changing anything underneath it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ledger import Ledger


@dataclass(frozen=True)
class CandidateAction:
    action_id: str
    expected_delta_efc: float  # E[delta NRS-EFC(a_t) | prefix]
    expected_delta_cost: float  # E[delta C_raw(a_t) | prefix]
    verified: bool = False  # backed by a deterministic checker/execution result
    non_redundant: bool = True  # passes the non-redundant-relevance gate


def roi(action: CandidateAction, d_task: float) -> float:
    """ROI(a_t) = E[delta NRS-EFC/D_task | prefix] / E[delta C_raw | prefix]"""
    normalized_gain = action.expected_delta_efc / max(d_task, 1e-9)
    return normalized_gain / max(action.expected_delta_cost, 1e-9)


class EFCAdapter:
    """A companion layer, not a replacement harness — nothing about the
    underlying model/tools/budget changes. It only decides which feedback
    to keep and when to stop spending."""

    def __init__(self, d_task: float, stop_threshold: float, window: int = 5):
        self.d_task = d_task
        self.stop_threshold = stop_threshold  # epsilon — fixed threshold (illustrative; tune per harness)
        self.window = window
        self.ledger = Ledger(d_task=d_task)
        self.durable_memory: list[str] = []
        self.scratch: list[str] = []

    def rank(self, candidates: list[CandidateAction]) -> list[CandidateAction]:
        """(1) Score each candidate by ROI, highest first."""
        return sorted(candidates, key=lambda a: roi(a, self.d_task), reverse=True)

    def retain(self, action: CandidateAction, actual_efc: float, actual_cost: float) -> None:
        """(2) Verified, non-redundant, high-scoring feedback -> durable
        memory. Unverified critiques stay in scratch space."""
        self.ledger.log(action.action_id, actual_efc, actual_cost)
        if action.verified and action.non_redundant:
            self.durable_memory.append(action.action_id)
        else:
            self.scratch.append(action.action_id)

    def should_gate_self_evolution(self, action_id: str) -> bool:
        """(3) Gate self-evolution on events that reliably improved
        raw-to-EFC conversion, not on coarse final reward — i.e. only
        events that made it to durable memory qualify."""
        return action_id in self.durable_memory

    def should_stop(self) -> bool:
        """(4) Stop/roll back when the recent window's normalized gain per
        unit cost drops under the fixed threshold — the budget is not
        exhausted, but useful feedback has saturated."""
        recent = self.ledger.rows[-self.window :]
        if len(recent) < self.window:
            return False
        recent_gain = sum(r.credit for r in recent) / max(self.d_task, 1e-9)
        recent_cost = sum(r.cost for r in recent)
        recent_roi = recent_gain / max(recent_cost, 1e-9)
        return recent_roi < self.stop_threshold
