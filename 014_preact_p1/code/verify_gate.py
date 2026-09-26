"""
verify_gate.py -- the store-time double gate (Section 3.3) and the
cache-miss fallback fix (Table 4), the mechanisms Part 2 of this episode is
about. Mirrors configs/verify_gate.yaml exactly.

Zero external dependencies -- Python 3.10+ stdlib only.

The point this file exists to make runnable: run-time verification
(state_machine.py's `replay`) checking that every action fired is NOT the
same question as "did this program actually do the job." A program can
reach `terminal_reached=True` with `coverage=1.0` and still have
accomplished nothing -- the paper's "coverage 100% / score 0" failure mode.
The store-time gate is a second, independent check, run once, before a
freshly compiled program is trusted into the corpus.
"""

from __future__ import annotations

from dataclasses import dataclass

from state_machine import Program, ReplayResult


@dataclass
class StoreDecision:
    stored: bool
    reason: str


def store_time_gate(replay_result: ReplayResult, evaluator_scored_pass: bool) -> StoreDecision:
    """The gate itself (paper, Section 3.3): stored only if BOTH hold --
    (1) the replay ran to its terminal state without error, AND
    (2) an independent evaluator scored a pass.

    Either one alone is not enough. Reaching the last state proves the
    machine walked its own graph; it proves nothing about the world.
    """
    replay_clean = replay_result.terminal_reached and not replay_result.error
    if replay_clean and evaluator_scored_pass:
        return StoreDecision(stored=True, reason="replay reached terminal cleanly AND evaluator scored a pass")
    if replay_clean and not evaluator_scored_pass:
        return StoreDecision(
            stored=False,
            reason=(
                f"REJECTED: replay reached terminal cleanly (coverage={replay_result.coverage:.0%}) "
                "but the evaluator scored 0 -- coverage 100% / score 0. Checking that an action fired "
                "is not the same as checking that the goal was met."
            ),
        )
    return StoreDecision(stored=False, reason="REJECTED: replay did not reach its terminal state cleanly")


class Corpus:
    """The corpus is mutative, not append-only (paper): a fresh program with
    the same dedup signature REPLACES the older one -- UPSERT, not append.
    """

    def __init__(self) -> None:
        self._programs: dict[str, Program] = {}
        self._rejected_this_run: set[str] = set()

    def upsert(self, program: Program, decision: StoreDecision) -> None:
        if decision.stored:
            self._programs[program.dedup_signature] = program
            self._rejected_this_run.discard(program.dedup_signature)
        else:
            # PreAct's original behavior: a rejected candidate is simply
            # deleted between runs -- the corpus ends up with NOTHING for
            # this task family, unlike Muscle-Mem's blind cache, which still
            # has a (blind) entry to fall back from.
            self._programs.pop(program.dedup_signature, None)
            self._rejected_this_run.add(program.dedup_signature)

    def lookup(self, dedup_signature: str) -> Program | None:
        return self._programs.get(dedup_signature)

    def was_rejected_this_run(self, dedup_signature: str) -> bool:
        return dedup_signature in self._rejected_this_run


def select_or_fresh_solve(corpus: Corpus, dedup_signature: str) -> str:
    """The Table 4 fallback fix: 'trigger a fresh CUA solve whenever the gate
    has emptied the corpus for a task' -- matching Muscle-Mem's cache-miss
    semantics exactly. Before the fix, PreAct's gate deleted a rejected
    program and left the next run with NO artifact at all (an outage, not a
    graceful fallback); after the fix, that empty slot behaves like any other
    cache miss and routes straight to a fresh agent solve.

    Effect on WebArena (paper, Table 4): warm SR 2.0/12 -> 6.25/12, exactly
    matching Muscle-Mem's blind-cache warm SR; Welch's t-test on the two
    warm-delta distributions gives |t| ~= 0.21, p ~= 0.84 -- statistically
    indistinguishable.
    """
    candidate = corpus.lookup(dedup_signature)
    if candidate is not None:
        return "replay_candidate"
    # covers both "never compiled yet" and "gate rejected it this run" --
    # the fix is that both cases resolve the same way, like a cache miss.
    return "fresh_cua_solve"
