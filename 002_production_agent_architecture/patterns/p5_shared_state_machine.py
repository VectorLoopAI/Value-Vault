#!/usr/bin/env python3
"""
P5 — Shared State Machine (State concern).

One durable versioned row is the source of truth. Workers are stateless and pure: they read
(state, action), propose the next state, and commit via compare-and-swap (CAS) against the row's
version. A stale write is rejected by the store, not silently applied.

Two details the video calls out as load-bearing (SEG 11):
  - "human_required" is a STATE, not a missing event — it lives in the same versioned row.
  - Every scheduled timer carries the version it was scheduled at, and must re-check that version
    before it fires — a timer that fires after a manual override has to see the override, not
    blindly overwrite it.

Failure signature to watch for in production (SEG 26's P5 row): workers retrying CAS more than
three times at p99 means the state row is too coarse-grained — split it into sub-state machines
per concern, rather than adding more retries.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable, Optional


class StaleWriteError(Exception):
    """Raised when a CAS write targets a version the store no longer holds."""


@dataclass
class VersionedRow:
    state: str
    version: int = 0
    data: dict = field(default_factory=dict)


class VersionedStateStore:
    """A minimal durable versioned-row store with compare-and-swap semantics.

    Swap this in-memory dict for Postgres (SELECT ... FOR UPDATE + version column),
    DynamoDB (conditional writes), or any store with atomic conditional updates.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._rows: dict[str, VersionedRow] = {}

    def create(self, row_id: str, initial_state: str, data: Optional[dict] = None) -> VersionedRow:
        with self._lock:
            row = VersionedRow(state=initial_state, version=0, data=data or {})
            self._rows[row_id] = row
            return row

    def read(self, row_id: str) -> VersionedRow:
        """Returns a detached snapshot, not the live object, so callers can't accidentally
        observe later mutations through a stale reference (a real store would return a
        fresh row from a SELECT, not a shared in-process object)."""
        with self._lock:
            live = self._rows[row_id]
            return VersionedRow(state=live.state, version=live.version, data=dict(live.data))

    def compare_and_swap(self, row_id: str, expected_version: int, next_state: str, data: dict) -> VersionedRow:
        """Commit `next_state` only if the row is still at `expected_version`. Raises on staleness.
        Returns a detached snapshot of the row after the commit."""
        with self._lock:
            row = self._rows[row_id]
            if row.version != expected_version:
                raise StaleWriteError(
                    f"row {row_id} expected version {expected_version}, actual {row.version}"
                )
            row.state = next_state
            row.data.update(data)
            row.version += 1
            return VersionedRow(state=row.state, version=row.version, data=dict(row.data))


@dataclass
class ScheduledTimer:
    """A timer that carries the version it was scheduled at (SEG 11's second load-bearing detail)."""

    row_id: str
    scheduled_at_version: int
    action: str


def fire_timer(store: VersionedStateStore, timer: ScheduledTimer, worker: Callable[[VersionedRow], tuple[str, dict]]):
    """Fire a timer, but re-check the version before writing — never an unconditional write.

    If a human override (or any other write) has moved the row past the version the timer was
    scheduled at, the CAS fails and the timer's effect is discarded rather than clobbering the
    override. This is exactly the P5 failure signature from SEG 26: "a timer fires after a manual
    override and produces a stale transition" happens when this check is skipped.
    """
    current = store.read(timer.row_id)
    if current.version != timer.scheduled_at_version:
        print(f"[timer discarded] row {timer.row_id} moved to v{current.version} "
              f"since timer was scheduled at v{timer.scheduled_at_version} (likely a human override)")
        return None
    next_state, data = worker(current)
    return store.compare_and_swap(timer.row_id, timer.scheduled_at_version, next_state, data)


if __name__ == "__main__":
    store = VersionedStateStore()
    store.create("renewal-123", initial_state="awaiting_signals", data={"offers_sent": 0})

    # A worker proposes the next state from (state, action) -- pure function, no side effects.
    def renewal_worker(row: VersionedRow) -> tuple[str, dict]:
        return "offer_sent", {"offers_sent": row.data["offers_sent"] + 1}

    row = store.read("renewal-123")
    next_state, data = renewal_worker(row)
    row = store.compare_and_swap("renewal-123", row.version, next_state, data)
    print(f"committed: state={row.state} version={row.version} data={row.data}")

    # A timer gets scheduled right now, carrying today's version...
    timer_scheduled_at_version = row.version
    scheduled_timer = ScheduledTimer(row_id="renewal-123", scheduled_at_version=timer_scheduled_at_version, action="auto_close")

    # ...but before it fires, a human override lands and bumps the version.
    store.compare_and_swap("renewal-123", row.version, "human_required", {"reason": "manual review"})

    # Now the timer fires: its version is stale relative to the override, so it must be discarded,
    # not applied blindly -- this is the exact CAS re-check the video calls out (SEG 11).
    fire_timer(store, scheduled_timer, renewal_worker)
    print(f"row state after override + stale timer fire: {store.read('renewal-123').state}")

    # A direct stale CAS raises, proving the store rejects out-of-date writes.
    try:
        store.compare_and_swap("renewal-123", expected_version=0, next_state="closed", data={})
    except StaleWriteError as e:
        print(f"stale write correctly rejected: {e}")
