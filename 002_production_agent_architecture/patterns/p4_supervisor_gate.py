#!/usr/bin/env python3
"""
P4 — Supervisor plus Gate (Control concern).

Two mechanisms run side by side (SEG 15):
  - Supervision restarts what dies, with exponential backoff, one-for-one (straight out of
    Erlang OTP semantics).
  - The Gate refuses out-of-policy writes BEFORE they reach an external system, as a purely
    deterministic rule check.

Three lines to remember, verbatim from the script: "the gate denies, the audit log records, the
supervisor restarts." And the two failure signatures the video warns about:
  1. Children keep hitting the same crash after repeated restarts -> it's not transient -> after
     max_restarts, escalate to a human, don't keep looping.
  2. The gate is slow -> it's running a model call -> the gate MUST be a deterministic check,
     full stop. This module enforces that by typing the gate's check as a plain function of
     primitives, never an async LLM call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class AuditEntry:
    ts: float
    kind: str  # "deny" | "restart" | "escalate"
    detail: str


class AuditLog:
    def __init__(self):
        self.entries: List[AuditEntry] = []

    def record(self, kind: str, detail: str) -> None:
        self.entries.append(AuditEntry(ts=time.time(), kind=kind, detail=detail))

    def __iter__(self):
        return iter(self.entries)


@dataclass
class PolicyRule:
    name: str
    check: Callable[[dict], bool]  # MUST be a pure deterministic function -- never a model call


class Gate:
    """Refuses out-of-policy writes before they reach an external system."""

    def __init__(self, rules: List[PolicyRule], audit: AuditLog):
        self.rules = rules
        self.audit = audit

    def check(self, proposed_write: dict) -> bool:
        for rule in self.rules:
            if not rule.check(proposed_write):
                self.audit.record("deny", f"rule '{rule.name}' rejected write {proposed_write}")
                return False
        return True


class MaxRestartsExceeded(Exception):
    pass


class Supervisor:
    """One-for-one restart with exponential backoff; escalates instead of looping forever."""

    def __init__(self, audit: AuditLog, max_restarts: int = 3, base_backoff_s: float = 0.01):
        self.audit = audit
        self.max_restarts = max_restarts
        self.base_backoff_s = base_backoff_s

    def run_supervised(
        self,
        worker: Callable[[], None],
        escalate: Callable[[str], None],
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        attempts = 0
        while True:
            try:
                worker()
                return
            except Exception as exc:  # noqa: BLE001 -- intentionally broad: any worker crash
                attempts += 1
                self.audit.record("restart", f"attempt {attempts} failed: {exc}")
                if attempts > self.max_restarts:
                    self.audit.record("escalate", f"max_restarts ({self.max_restarts}) exceeded")
                    escalate(f"worker failed {attempts} times, last error: {exc}")
                    raise MaxRestartsExceeded(str(exc)) from exc
                backoff = self.base_backoff_s * (2 ** (attempts - 1))
                sleep_fn(backoff)


if __name__ == "__main__":
    audit = AuditLog()

    # Gate: deterministic rules only -- no model call, ever.
    gate = Gate(
        rules=[
            PolicyRule("max_discount_pct", lambda write: write.get("discount_pct", 0) <= 30),
            PolicyRule("requires_customer_id", lambda write: "customer_id" in write),
        ],
        audit=audit,
    )

    good_write = {"customer_id": "cust_1", "discount_pct": 15}
    bad_write = {"customer_id": "cust_2", "discount_pct": 90}  # the video's 90% discount scenario

    print(f"good write allowed: {gate.check(good_write)}")
    print(f"bad write allowed:  {gate.check(bad_write)}")

    # Supervisor: restart a persistently-crashing worker until max_restarts, then escalate.
    supervisor = Supervisor(audit=audit, max_restarts=2, base_backoff_s=0.0)  # no real sleep in the demo

    call_count = {"n": 0}

    def always_crashing_worker() -> None:
        call_count["n"] += 1
        raise RuntimeError("same crash every time -- not transient")

    def escalate_to_human(message: str) -> None:
        print(f"ESCALATED TO HUMAN: {message}")

    try:
        supervisor.run_supervised(always_crashing_worker, escalate_to_human, sleep_fn=lambda s: None)
    except MaxRestartsExceeded as e:
        print(f"gave up after max_restarts, correctly did not loop forever: {e}")

    print("\naudit trail (gate denies, supervisor restarts, escalations):")
    for entry in audit:
        print(f"  [{entry.kind}] {entry.detail}")
