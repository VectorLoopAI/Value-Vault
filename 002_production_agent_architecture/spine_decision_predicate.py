#!/usr/bin/env python3
"""
Step 2 of the five-step methodology, as a runnable predicate: "Choose the spine."

Select P5 (Shared State Machine) iff ALL three are true:
  1. pauses longer than one hour, or external waits are involved
  2. the state at any pause is NOT fully reconstructible from the original input
  3. the world can change while the process is paused

If only (1) fails            -> P3 (Event-Driven Sequencing) is sufficient.
If (2) fails                 -> no durable spine needed at all; reconstruct state on demand.
If (3) fails (but 1 & 2 hold)-> P3-vs-P5 reduces to a cost question, not a correctness one.

This is the exact decision function the video (SEG 18, SEG 23-24) walks through the Port-In
vs. Lead-Warming contrast with: same runtime class (Long-Horizon), different spine, because
predicate (2) differs.
"""

from dataclasses import dataclass
from enum import Enum


class Spine(str, Enum):
    P3_EVENT_DRIVEN = "P3 — Event-Driven Sequencing"
    P5_STATE_MACHINE = "P5 — Shared State Machine"
    NO_DURABLE_SPINE = "no durable spine needed — reconstruct on demand"
    COST_TRADE_OFF = "P3-vs-P5 is a cost question here, not a correctness one"


@dataclass
class SpineWorkload:
    name: str
    pauses_over_one_hour_or_external_waits: bool
    state_reconstructible_from_input: bool  # True = CAN rebuild from input/log
    world_changes_during_pause: bool


def choose_spine(w: SpineWorkload) -> Spine:
    """Step 2 predicate. Returns the chosen spine pattern and why."""
    long_pause = w.pauses_over_one_hour_or_external_waits
    reconstructible = w.state_reconstructible_from_input
    world_moves = w.world_changes_during_pause

    if not long_pause:
        return Spine.P3_EVENT_DRIVEN
    if reconstructible:
        return Spine.NO_DURABLE_SPINE
    if not world_moves:
        return Spine.COST_TRADE_OFF
    # long_pause True, reconstructible False, world_moves True -> all three hold
    return Spine.P5_STATE_MACHINE


if __name__ == "__main__":
    # The video's Table-7 contrast: same runtime class, different spine.
    examples = [
        SpineWorkload(
            name="Number Port-In Coordination (Long-Horizon)",
            pauses_over_one_hour_or_external_waits=True,
            state_reconstructible_from_input=False,  # carrier-ack / pool-reserved / SLA-timer isn't rebuildable
            world_changes_during_pause=True,          # donating carrier can reject mid-flight
        ),
        SpineWorkload(
            name="Lead Warming drip campaign (Long-Horizon)",
            pauses_over_one_hour_or_external_waits=True,
            state_reconstructible_from_input=True,   # touch log + current score rebuilds everything
            world_changes_during_pause=True,
        ),
        SpineWorkload(
            name="Contract Renewal, 90-day window (Long-Horizon)",
            pauses_over_one_hour_or_external_waits=True,
            state_reconstructible_from_input=False,  # mid-window signals aren't in the original input
            world_changes_during_pause=True,          # product EOL at day -47
        ),
        SpineWorkload(
            name="Billing & Payment Assist (Conversational)",
            pauses_over_one_hour_or_external_waits=False,  # session is short
            state_reconstructible_from_input=True,
            world_changes_during_pause=False,
        ),
    ]

    for w in examples:
        print(f"{w.name}\n  -> {choose_spine(w).value}\n")
