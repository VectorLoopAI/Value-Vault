#!/usr/bin/env python3
"""
P2 — Scatter-Gather plus Saga (Coordination concern).

A coordinator fans out to symmetric peers with side-effects and aggregates their results. Each
peer logs a compensating action so that if a later peer fails after an earlier one already wrote
somewhere durable (e.g. billing), the coordinator can unwind: compensations run in strict
REVERSE order, and every compensation must be idempotent (SEG 14).

The trap the video calls out: compensation logic outgrows the original action. The fix is NOT to
grow the saga -- it's to split the original action into smaller steps, each with its own narrow
compensation (SEG 14, SEG 26's P2 signature).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


class PeerFailure(Exception):
    def __init__(self, peer_name: str, cause: str):
        super().__init__(f"peer '{peer_name}' failed: {cause}")
        self.peer_name = peer_name


@dataclass
class Peer:
    name: str
    action: Callable[[], dict]           # the side-effecting action (e.g. write to billing)
    compensate: Callable[[dict], None]   # MUST be idempotent -- may be called more than once


@dataclass
class SagaResult:
    committed: List[str] = field(default_factory=list)
    compensated: List[str] = field(default_factory=list)
    failed_peer: Optional[str] = None


class ScatterGatherSaga:
    """P2: fan out to peers, and if any fails, unwind in strict reverse commit order."""

    def run(self, peers: List[Peer]) -> SagaResult:
        result = SagaResult()
        committed_peers: List[tuple[Peer, dict]] = []

        try:
            for peer in peers:
                output = peer.action()
                committed_peers.append((peer, output))
                result.committed.append(peer.name)
        except PeerFailure as failure:
            result.failed_peer = failure.peer_name
            # Unwind in STRICT REVERSE order of commit -- never forward, never out of order.
            for peer, output in reversed(committed_peers):
                peer.compensate(output)  # must be idempotent: may run again on a retried unwind
                result.compensated.append(peer.name)

        return result


if __name__ == "__main__":
    billing_writes: List[str] = []

    def contract_action() -> dict:
        billing_writes.append("charge-created")
        return {"billing_id": "chg_001"}

    def contract_compensate(output: dict) -> None:
        # idempotent: safe to call even if already reversed
        if "chg_001" in billing_writes:
            billing_writes.remove("chg_001")
            print(f"compensated billing write {output['billing_id']}")

    def offer_action() -> dict:
        return {"offer_id": "off_001"}

    def offer_compensate(output: dict) -> None:
        print(f"compensated offer {output['offer_id']} (no-op, no side effect to undo)")

    def flaky_peer_action() -> dict:
        raise PeerFailure("network_validation", "timeout reaching carrier API")

    def flaky_peer_compensate(output: dict) -> None:
        pass  # never committed, nothing to compensate

    saga = ScatterGatherSaga()
    peers = [
        Peer("offer_drafting", offer_action, offer_compensate),
        Peer("contract_billing", contract_action, contract_compensate),
        Peer("network_validation", flaky_peer_action, flaky_peer_compensate),
    ]

    result = saga.run(peers)
    print(f"committed: {result.committed}")
    print(f"failed at: {result.failed_peer}")
    print(f"compensated (reverse order): {result.compensated}")
    assert billing_writes == [], "billing write should have been fully compensated"
    print("billing state clean after unwind:", billing_writes)
