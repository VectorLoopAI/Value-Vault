#!/usr/bin/env python3
"""
P6 — Human in the Loop (Control concern).

Four control planes, not one (SEG 16), all emitting to a single audit trail:
  - Kill switch  -- revokes a cancellation token in ~1 second.
  - Escalation   -- calls suspend(reason) and writes a durable row a human reviews later.
  - Approval     -- a synchronous wait under SLA, falling back to a conservative DENY when the
                    clock runs out.
  - Throttling   -- refuses work that would exceed a per-minute/per-day blast-radius cap.

The video's wisest line, verbatim: "you don't need all four at version one. You DO need to
record which ones you're deferring, and why." This module makes each plane an independently
toggleable object precisely so a v1 build can wire up only what it needs and log the rest.

P6 failure signatures from SEG 26 to watch for:
  - Approval SLAs missed and everything falls back to deny -> reviewer queue is overloaded ->
    an organizational fix, not a code fix (the audit trail is what makes this visible).
  - Kill switch revoked but workers keep running -> workers only checked the token at workflow
    start, not at every tool boundary. This module checks at every `call()`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class AuditEvent:
    ts: float
    plane: str
    detail: str


class AuditTrail:
    def __init__(self):
        self.events: List[AuditEvent] = []

    def record(self, plane: str, detail: str) -> None:
        self.events.append(AuditEvent(time.time(), plane, detail))


class CancellationToken:
    """Kill switch: revocation must be checked at EVERY tool boundary, not just workflow start."""

    def __init__(self):
        self._revoked = False

    def revoke(self) -> None:
        self._revoked = True

    @property
    def is_revoked(self) -> bool:
        return self._revoked


class KillSwitchViolation(Exception):
    pass


def call_with_kill_switch(token: CancellationToken, audit: AuditTrail, tool_name: str, fn: Callable[[], None]) -> None:
    """Every tool boundary re-checks the token -- the fix for the P6 signature in SEG 26."""
    if token.is_revoked:
        audit.record("kill_switch", f"blocked call to '{tool_name}': token already revoked")
        raise KillSwitchViolation(f"cancellation token revoked; refusing to call '{tool_name}'")
    fn()


@dataclass
class DurableEscalationRow:
    reason: str
    reviewed: bool = False


class Escalation:
    def __init__(self, audit: AuditTrail):
        self.audit = audit
        self.queue: List[DurableEscalationRow] = []

    def suspend(self, reason: str) -> DurableEscalationRow:
        row = DurableEscalationRow(reason=reason)
        self.queue.append(row)
        self.audit.record("escalation", f"suspended: {reason}")
        return row


class Approval:
    """Synchronous wait under SLA; falls back to a conservative DENY when the clock runs out."""

    def __init__(self, audit: AuditTrail, sla_seconds: float):
        self.audit = audit
        self.sla_seconds = sla_seconds

    def request(self, description: str, human_decision_fn: Callable[[], Optional[bool]], clock: Callable[[], float] = time.monotonic) -> bool:
        start = clock()
        decision = human_decision_fn()  # in production: poll a queue/webhook until SLA elapses
        elapsed = clock() - start
        if elapsed > self.sla_seconds or decision is None:
            self.audit.record("approval", f"SLA missed for '{description}' -> conservative DENY")
            return False
        self.audit.record("approval", f"'{description}' decided: {decision}")
        return decision


class BlastRadiusExceeded(Exception):
    pass


class Throttle:
    """Refuses work that would exceed a per-minute or per-day blast-radius cap."""

    def __init__(self, audit: AuditTrail, per_minute_cap: int):
        self.audit = audit
        self.per_minute_cap = per_minute_cap
        self._window_start = time.monotonic()
        self._count = 0

    def allow(self, action_name: str, clock: Callable[[], float] = time.monotonic) -> bool:
        now = clock()
        if now - self._window_start >= 60:
            self._window_start = now
            self._count = 0
        if self._count >= self.per_minute_cap:
            self.audit.record("throttle", f"blocked '{action_name}': per-minute cap {self.per_minute_cap} exceeded")
            return False
        self._count += 1
        return True


@dataclass
class HumanInTheLoopConfig:
    """Which of the four planes are active in this build, and why the rest are deferred (SEG 16)."""

    kill_switch_enabled: bool = True
    escalation_enabled: bool = True
    approval_enabled: bool = False
    throttling_enabled: bool = False
    deferred_reason: Dict[str, str] = field(default_factory=dict)


if __name__ == "__main__":
    audit = AuditTrail()

    config = HumanInTheLoopConfig(
        approval_enabled=False,
        throttling_enabled=False,
        deferred_reason={
            "approval": "v1 has no financially-consequential writes yet -- deferred, tracked here",
            "throttling": "single-tenant pilot, no blast-radius risk yet -- deferred, tracked here",
        },
    )
    print("v1 control planes:", {
        "kill_switch": config.kill_switch_enabled,
        "escalation": config.escalation_enabled,
        "approval": config.approval_enabled,
        "throttling": config.throttling_enabled,
    })
    print("deferred, with reasons:", config.deferred_reason)

    # Kill switch demo: revoke, then confirm a subsequent tool call is refused at the boundary.
    token = CancellationToken()
    call_with_kill_switch(token, audit, "send_offer_email", lambda: print("sent offer email"))
    token.revoke()
    try:
        call_with_kill_switch(token, audit, "charge_billing", lambda: print("charged billing"))
    except KillSwitchViolation as e:
        print(f"correctly blocked post-revocation call: {e}")

    # Escalation demo.
    escalation = Escalation(audit)
    escalation.suspend("account merger detected mid-renewal")

    # Approval demo: SLA missed -> conservative deny.
    approval = Approval(audit, sla_seconds=0.0)
    approved = approval.request("apply 40% retention discount", human_decision_fn=lambda: True)
    print(f"approval result (SLA=0s, should deny): {approved}")

    print("\naudit trail:")
    for e in audit.events:
        print(f"  [{e.plane}] {e.detail}")
