#!/usr/bin/env python3
"""
Quarterly drift-diagnostic procedure (SEG 26).

Run on a sampled batch of production failures to tell apart the three "diseases" that get
lumped together as "it's flaky" (SEG 25):

  - Variance             - per-call non-determinism at fixed inputs; shrinks with model generation.
  - Architectural momentum - the reliability trajectory over calendar time (not diagnosed per-batch;
                             it's the *reason* momentum-shaped failures compound, see the video's
                             y(t) = mu*t + sigma*xi(t) framing).
  - Replay divergence     - same input event, different downstream events on a newer model version.
                             The migration trigger from P3 (event log) to P5 (versioned state machine).

Procedure:
  1. Pin the model version that produced the most recent failure batch.
  2. Replay the failures on the PRIOR model version.
  3. Branch:
     - failures PERSIST on the prior version -> functional failure -> consult the signature catalog.
     - failures RESOLVE on the prior version  -> replay divergence  -> consider migrating P3 -> P5.
     - NEITHER version reproduces the failure -> variance          -> raise k in pass@k and observe.

Caveat the paper is explicit about: this assumes you CAN replay against a prior model checkpoint.
Some hosted models don't preserve prior checkpoints, which blocks step 2 entirely.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List


class Diagnosis(str, Enum):
    FUNCTIONAL_FAILURE = "functional failure -> consult the P1-P6 signature catalog"
    REPLAY_DIVERGENCE = "replay divergence -> spine is exposed; consider migrating P3 -> P5"
    VARIANCE = "variance -> raise k in pass@k and observe"
    BLOCKED_NO_PRIOR_CHECKPOINT = "blocked -> cannot replay a prior checkpoint for this model"


@dataclass
class FailureCase:
    case_id: str
    input_event: dict
    current_model_version: str
    prior_model_version: str | None  # None if the host doesn't retain prior checkpoints


def diagnose(
    case: FailureCase,
    replay_fn: Callable[[dict, str], bool],
    persists_on_prior: bool | None = None,
) -> Diagnosis:
    """
    replay_fn(input_event, model_version) -> True if the SAME failure reproduces on that version.
    In production this calls your actual agent runtime pinned to `model_version`; here it's
    injected so the module is testable without a live model.
    """
    if case.prior_model_version is None:
        return Diagnosis.BLOCKED_NO_PRIOR_CHECKPOINT

    fails_on_prior = replay_fn(case.input_event, case.prior_model_version)

    if fails_on_prior:
        return Diagnosis.FUNCTIONAL_FAILURE
    # doesn't fail on prior version -- did it fail on current at all (should be True by definition
    # of "this is a failure case"), so absence of failure-on-prior means either divergence or variance.
    fails_on_current_again = replay_fn(case.input_event, case.current_model_version)
    if fails_on_current_again:
        return Diagnosis.REPLAY_DIVERGENCE
    return Diagnosis.VARIANCE


def run_quarterly_batch(cases: List[FailureCase], replay_fn: Callable[[dict, str], bool]) -> dict:
    """Runs the full batch and returns a tally, mirroring what you'd put on the Compliance lens."""
    tally: dict[str, int] = {}
    for case in cases:
        diagnosis = diagnose(case, replay_fn)
        tally[diagnosis.value] = tally.get(diagnosis.value, 0) + 1
    return tally


if __name__ == "__main__":
    # A fake replay function standing in for "run the agent pinned to this model version against
    # this input event and report whether the SAME failure reproduces." Wire this to your real
    # eval harness (Promptfoo, your own harness, etc.) in production.
    def demo_replay(event: dict, model_version: str) -> bool:
        # deliberately fabricated behavior for the demo:
        #  - "gate_bypass" cases are functional bugs -> fail on every version
        #  - "prompt_injection" cases are model-version-dependent -> only fail on newer models
        #  - "flaky_retry" cases never reliably reproduce -> pure variance
        kind = event.get("kind")
        if kind == "gate_bypass":
            return True
        if kind == "prompt_injection":
            return model_version >= "gpt-4.1"
        return False

    batch = [
        FailureCase("case-001", {"kind": "gate_bypass"}, "gpt-4.1", "gpt-4o"),
        FailureCase("case-002", {"kind": "prompt_injection"}, "gpt-4.1", "gpt-4o"),
        FailureCase("case-003", {"kind": "flaky_retry"}, "gpt-4.1", "gpt-4o"),
        FailureCase("case-004", {"kind": "prompt_injection"}, "claude-hosted", None),
    ]

    for case in batch:
        print(f"{case.case_id}: {diagnose(case, demo_replay).value}")

    print("\nQuarterly tally:")
    for diagnosis, count in run_quarterly_batch(batch, demo_replay).items():
        print(f"  {count}x  {diagnosis}")
