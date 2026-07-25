#!/usr/bin/env python3
"""
P3 — Event-Driven Sequencing (State concern).

An append-only log is the source of truth; consumers subscribe, react, and emit new events.
The log itself is deterministic and perfectly replayable -- but LLM-based *consumers* reading it
are not. SEG 12's failure mode, named precisely: the same input event, replayed months later on
a newer model, can produce a different downstream event. Same bytes in the log, different real-
world outcome. That's **replay divergence** -- and it's the diagnostic trigger to migrate the
spine from P3 to P5 (see spine_decision_predicate.py and diagnostic_procedure.py).

This module also implements watermarking, the fix for P3's other failure signature from the
SEG 26 catalog: out-of-order events producing wrong outcomes because consumers don't reject
events older than the current watermark.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass(frozen=True)
class Event:
    seq: int
    event_time: float  # logical/business timestamp, not wall-clock append time
    kind: str
    payload: dict


class EventLog:
    """Append-only, replayable, branchable. Never mutated in place."""

    def __init__(self):
        self._events: List[Event] = []

    def append(self, event_time: float, kind: str, payload: dict) -> Event:
        event = Event(seq=len(self._events), event_time=event_time, kind=kind, payload=payload)
        self._events.append(event)
        return event

    def replay(self, from_seq: int = 0) -> List[Event]:
        """Replay is just re-reading the log -- the log itself never changes."""
        return list(self._events[from_seq:])


class WatermarkedConsumer:
    """Rejects events older than the current watermark instead of applying them out of order."""

    def __init__(self, on_event: Callable[[Event], Optional[Event]]):
        self._on_event = on_event
        self.watermark: float = float("-inf")
        self.audit_log: List[str] = []
        self.emitted: List[Event] = []

    def consume(self, event: Event) -> Optional[Event]:
        if event.event_time < self.watermark:
            self.audit_log.append(
                f"REJECTED late event seq={event.seq} event_time={event.event_time} "
                f"< watermark={self.watermark}"
            )
            return None
        self.watermark = max(self.watermark, event.event_time)
        return self._on_event(event)


def replay_and_check_divergence(
    log: EventLog,
    consumer_factory_v1: Callable[[], WatermarkedConsumer],
    consumer_factory_v2: Callable[[], WatermarkedConsumer],
) -> bool:
    """Replay the same log through two consumer "model versions" and report whether their
    emitted downstream events diverge -- the concrete replay-divergence check from SEG 12/26.
    """
    events = log.replay()
    c1, c2 = consumer_factory_v1(), consumer_factory_v2()
    emitted_v1 = [c1.consume(e) for e in events]
    emitted_v2 = [c2.consume(e) for e in events]
    diverged = emitted_v1 != emitted_v2
    return diverged


if __name__ == "__main__":
    log = EventLog()
    log.append(event_time=1.0, kind="usage_drop", payload={"pct": 30})
    log.append(event_time=2.0, kind="billing_change", payload={"delta": -12.0})
    log.append(event_time=1.5, kind="late_signal", payload={"note": "arrived out of order"})

    def make_consumer_v1() -> WatermarkedConsumer:
        # "older model": conservative interpretation
        def handle(event: Event) -> Optional[Event]:
            if event.kind == "usage_drop" and event.payload["pct"] >= 25:
                return Event(seq=-1, event_time=event.event_time, kind="flag_at_risk", payload={})
            return None
        return WatermarkedConsumer(handle)

    def make_consumer_v2() -> WatermarkedConsumer:
        # "newer model": more aggressive interpretation of the identical event -- this is the
        # replay-divergence scenario: same log, different downstream event.
        def handle(event: Event) -> Optional[Event]:
            if event.kind == "usage_drop" and event.payload["pct"] >= 20:
                return Event(seq=-1, event_time=event.event_time, kind="trigger_retention_offer", payload={})
            return None
        return WatermarkedConsumer(handle)

    diverged = replay_and_check_divergence(log, make_consumer_v1, make_consumer_v2)
    print(f"replay divergence detected: {diverged}")
    if diverged:
        print("  -> same log, different downstream events across model versions.")
        print("  -> per the methodology: consider migrating this spine from P3 to P5.")

    # Watermark rejection demo, independent of the divergence check above.
    watermarked = make_consumer_v1()
    for event in log.replay():
        watermarked.consume(event)
    for line in watermarked.audit_log:
        print(line)
