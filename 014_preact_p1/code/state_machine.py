"""
state_machine.py -- a runnable reference implementation of PreAct's program
representation and run-time replay ("observe first, then act"), Section 3.2
of "PreAct: Computer-Using Agents That Get Faster On Repeated Tasks"
(Bojie Li, Pine AI, arXiv:2606.17929v1).

Zero external dependencies -- Python 3.10+ stdlib only. The program data
below mirrors configs/contacts_add_contact.program.yaml exactly (Listing 1 /
Figure 4, the "Emilia Gonzalez program" named throughout both episodes) --
embedded directly in Python here so the demo needs no YAML parser.

This module deliberately implements ONLY run-time verification (checking a
state's predicate before firing the transition out of it). It does NOT
implement the store-time gate -- that is verify_gate.py, the Part 2 mechanism.
Keeping them in separate files mirrors the paper's own point: these are two
different checks, run at two different moments.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class State:
    id: str
    verify: dict | None   # predicate spec checked against the live screen; None only for the terminal state
    terminal: bool = False


@dataclass(frozen=True)
class Transition:
    src: str
    dst: str
    action: dict


@dataclass(frozen=True)
class Program:
    task_family: str
    dedup_signature: str
    parameters: list[str]
    states: list[State]
    transitions: list[Transition]

    def state(self, state_id: str) -> State:
        for s in self.states:
            if s.id == state_id:
                return s
        raise KeyError(f"no such state: {state_id}")

    def transition_from(self, state_id: str) -> Transition | None:
        for t in self.transitions:
            if t.src == state_id:
                return t
        return None


# ---------------------------------------------------------------------------
# The Emilia Gonzalez program (Listing 1 / Figure 4, ContactsAddContact).
# Mirrors configs/contacts_add_contact.program.yaml exactly.
# ---------------------------------------------------------------------------

CONTACTS_ADD_CONTACT = Program(
    task_family="ContactsAddContact",
    dedup_signature="android.contacts.add_contact.v1",
    parameters=["first_name", "last_name", "phone_number"],
    states=[
        State("contacts_app_open", {"predicate": "expect_element", "resource_id": "...floating_action_button"}),
        State("create_contact_form", {"predicate": "expect_element", "element": "first-name EditText"}),
        State("first_name_entered", {"predicate": "expect_element", "element": "last-name field"}),
        State("last_name_entered", {"predicate": "expect_element", "element": "phone field"}),
        State("phone_entered", {"predicate": "expect_element", "element": "mobile phone-type selector"}),
        State("phone_type_selected", {"predicate": "expect_element", "element": "Save button"}),
        State("contact_saved", None, terminal=True),
    ],
    transitions=[
        Transition("contacts_app_open", "create_contact_form", {"kind": "click", "target": "floating_action_button"}),
        Transition("create_contact_form", "first_name_entered", {"kind": "type", "target": "first_name_field", "value_param": "first_name"}),
        Transition("first_name_entered", "last_name_entered", {"kind": "type", "target": "last_name_field", "value_param": "last_name"}),
        Transition("last_name_entered", "phone_entered", {"kind": "type", "target": "phone_field", "value_param": "phone_number"}),
        Transition("phone_entered", "phone_type_selected", {"kind": "click", "target": "mobile_phone_type_selector"}),
        Transition("phone_type_selected", "contact_saved", {"kind": "click", "target": "save_button"}),
    ],
)


@dataclass
class ReplayResult:
    states_visited: list[str] = field(default_factory=list)
    terminal_reached: bool = False
    halted_at: str | None = None          # state whose predicate mismatched, if any
    error: bool = False
    coverage: float = 0.0                 # states_visited / total states


def replay(program: Program, screen_checks: dict[str, bool]) -> ReplayResult:
    """Walk `program` from its first state, firing each transition only when
    the CURRENT state's predicate matches the live screen -- "observe first,
    then act" (paper, Section 3.2).

    `screen_checks` maps state id -> whether that state's predicate matches
    the live screen at the moment replay reaches it. This is the same
    boolean a real replayer would get back from evaluating a predicate
    against a live screenshot / accessibility tree; here it's supplied
    directly so the demo is deterministic and dependency-free.

    Returns a ReplayResult. Reaching the terminal state with coverage 1.0
    proves the program executed every action -- it proves NOTHING about
    whether the task's goal was actually met. That's the whole reason
    verify_gate.py exists as a second, separate check.
    """
    result = ReplayResult()
    current = program.states[0].id
    total = len(program.states)

    while True:
        state = program.state(current)
        matched = screen_checks.get(current, False)
        if not matched:
            result.halted_at = current
            result.coverage = len(result.states_visited) / total
            return result

        result.states_visited.append(current)

        if state.terminal:
            result.terminal_reached = True
            result.coverage = len(result.states_visited) / total
            return result

        transition = program.transition_from(current)
        if transition is None:
            result.error = True
            result.coverage = len(result.states_visited) / total
            return result

        # action fires -- zero model calls (the speed source)
        current = transition.dst
