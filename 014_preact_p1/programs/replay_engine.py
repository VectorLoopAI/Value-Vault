"""
replay_engine.py -- a small, dependency-light implementation of PreAct's two
core mechanisms from "PreAct: Computer-Using Agents That Get Faster on
Repeated Tasks" (Bojie Li, Pine AI, arXiv:2606.17929v1):

  1. Run-time verification (Part 1, SEG 09): "observe first, then act."
     Before firing a transition, check that state's verification predicate
     against the live screen. Match -> fire the action, no model call.
     Mismatch -> halt and hand control back to a fallback agent.

  2. The store-time verify gate (Part 2, SEG 03-04): a candidate program is
     UPSERTed into the corpus only if BOTH hold -- the replay runs to its
     terminal state without error, AND an independent evaluator scores the
     resulting world-state a pass. Either check alone is not enough; that's
     the paper's whole insight (the cov=100%/score=0 failure mode).

This loads a program spec (see ../programs/contacts_add_contact.yaml) and
replays it against a pluggable `screen` object -- in this demo, a simple
in-memory dict standing in for "the live screen state." Swap `screen` for a
real accessibility-tree reader / vision call and this is the actual
mechanism, not pseudocode.

Zero external dependencies beyond PyYAML (`pip install pyyaml`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import yaml


@dataclass
class ReplayResult:
    reached_terminal: bool
    states_visited: list[str] = field(default_factory=list)
    model_calls: int = 0
    halted_at: Optional[str] = None
    reason: Optional[str] = None


class Program:
    """A loaded PreAct program: P = (S, T, M, V)."""

    def __init__(self, spec: dict[str, Any]):
        self.metadata = spec["metadata"]
        self.states = {s["id"]: s for s in spec["states"]}
        self.transitions = spec["transitions"]
        self.extraction_predicates = spec.get("extraction_predicates", [])

    @classmethod
    def from_yaml(cls, path: str) -> "Program":
        with open(path, "r") as f:
            return cls(yaml.safe_load(f))

    def transitions_from(self, state_id: str) -> list[dict]:
        return [t for t in self.transitions if t["source"] == state_id]

    def start_state(self) -> str:
        # First state declared that is not the destination of any transition.
        destinations = {t["destination"] for t in self.transitions}
        for s in self.states:
            if s not in destinations:
                return s
        return next(iter(self.states))


def default_predicate_checker(screen: dict, verify: dict) -> bool:
    """Checks a state's `verify.predicate` against a mock `screen` dict.

    `screen` is expected to carry a set of currently-visible element ids/
    resource ids under `screen["visible_elements"]`. This stands in for a
    real accessibility-tree read or vision-model call in production.
    """
    if verify["predicate"] != "expect_element":
        raise NotImplementedError(f"Unknown predicate: {verify['predicate']}")
    target = verify.get("resource_id") or verify.get("element")
    return target in screen.get("visible_elements", set())


def replay(
    program: Program,
    screen: dict,
    apply_action: Callable[[dict, dict], dict],
    predicate_checker: Callable[[dict, dict], bool] = default_predicate_checker,
) -> ReplayResult:
    """Run-time verification loop: 'observe first, then act.'

    `apply_action(screen, action)` must return the *new* screen dict after
    firing `action` -- in production this is where the click/type/navigate
    actually happens. Halts (does not raise) the moment a predicate check
    fails, exactly like the paper's replay-halts-and-hands-off behavior.
    """
    state_id = program.start_state()
    visited = []

    while True:
        state = program.states[state_id]
        if not predicate_checker(screen, state["verify"]):
            return ReplayResult(
                reached_terminal=False,
                states_visited=visited,
                halted_at=state_id,
                reason="predicate mismatch -- handing off to fallback agent",
            )
        visited.append(state_id)

        if state.get("terminal"):
            return ReplayResult(reached_terminal=True, states_visited=visited)

        outgoing = program.transitions_from(state_id)
        if not outgoing:
            return ReplayResult(
                reached_terminal=False,
                states_visited=visited,
                halted_at=state_id,
                reason="no outgoing transition and state is not terminal",
            )
        # PreAct tolerates redundant duplicate transitions out of one state
        # (see contacts_app_open in the Emilia Gonzalez program) -- take the
        # first that fires cleanly.
        transition = outgoing[0]
        screen = apply_action(screen, transition["action"])
        state_id = transition["destination"]


def verify_before_store(
    program: Program,
    reset_environment: Callable[[], dict],
    apply_action: Callable[[dict, dict], dict],
    evaluator: Callable[[dict], bool],
) -> tuple[bool, ReplayResult]:
    """The store-time gate (Part 2). Stored only if BOTH hold:
      (a) replay reaches its terminal state without error, AND
      (b) an independent evaluator scores the resulting world-state a pass.

    This is deliberately separate from `replay()`'s own success signal --
    reaching the terminal state proves the machine walked its own graph; it
    proves nothing about whether the goal was actually met (the
    coverage=100%/score=0 failure this gate exists to catch).
    """
    clean_screen = reset_environment()
    result = replay(program, clean_screen, apply_action)
    if not result.reached_terminal:
        return False, result
    goal_met = evaluator(clean_screen)
    return (result.reached_terminal and goal_met), result


if __name__ == "__main__":
    # Minimal smoke test using the Emilia Gonzalez program with a mock screen
    # that always matches (a "textbook" happy-path replay).
    import os

    program = Program.from_yaml(
        os.path.join(os.path.dirname(__file__), "contacts_add_contact.yaml")
    )
    all_ids = {"floating_action_button", "add_contact_shortcut", "first_name_field",
               "last_name_field", "phone_field", "phone_type_selector",
               "save_button", "contact_detail_view"}
    screen = {"visible_elements": all_ids}  # a screen that "matches everything"

    def apply_action(screen, action):
        return screen  # no-op mock -- real version drives the device/browser

    result = replay(program, screen, apply_action)
    print(f"reached_terminal={result.reached_terminal}, "
          f"states_visited={result.states_visited}, model_calls={result.model_calls}")
