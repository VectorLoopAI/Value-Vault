"""
acceptance_rule.py — Self-Harness Stage 3: Proposal Validation.

Implements the acceptance rule for promoting a candidate harness edit:

    accept(delta_in, delta_ho) := (delta_in >= 0) AND (delta_ho >= 0)
                                   AND (max(delta_in, delta_ho) > 0)

In plain terms: a candidate is promoted only if it does not hurt either the
held-in split (D_in) or the held-out split (D_ho), AND it meaningfully helps
at least one of them. A proposal that trades held-in gains for held-out
losses (or vice versa) is rejected, even if the total pass count technically
goes up.

Also implements the stochastic-evaluation variant: under noisy pass/fail
evaluation, repeat each candidate's evaluation N times and apply the rule to
the aggregated (averaged) deltas, so a single lucky/unlucky run can't flip
the decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class SplitResult:
    """Pass rate (0-100 %) for one harness on one split."""
    pass_pct: float


@dataclass
class CandidateResult:
    candidate_id: str
    delta_in: float   # P_in(h_t^(j)) - P_in(h_t)
    delta_ho: float   # P_ho(h_t^(j)) - P_ho(h_t)


def accept(delta_in: float, delta_ho: float) -> bool:
    """The core acceptance rule. Memorize this one."""
    return delta_in >= 0 and delta_ho >= 0 and max(delta_in, delta_ho) > 0


def accept_stochastic(delta_in_runs: list[float], delta_ho_runs: list[float]) -> bool:
    """
    Aggregate repeated stochastic-evaluation runs before applying the rule,
    per the paper: "candidate evaluation is repeated and the rule applied to
    aggregated pass counts, reducing the chance a fluke run gets promoted."
    """
    return accept(mean(delta_in_runs), mean(delta_ho_runs))


def validate_round(current_pass: dict, candidates: list[CandidateResult]) -> list[str]:
    """
    Stage 3 over a full round: evaluate every candidate, return the IDs of
    every promoted candidate. If none are promoted, h_{t+1} = h_t (no change).
    If multiple pass, the caller is expected to MERGE all of their edits into
    h_{t+1} (merging itself is edit-representation-specific and left to the
    harness's own diff/patch format).
    """
    promoted = [c.candidate_id for c in candidates if accept(c.delta_in, c.delta_ho)]
    return promoted


if __name__ == "__main__":
    # Reproduces the video's headline acceptance-rule walkthrough (SEG 15)
    # plus the main-results table numbers (SEG 27) recast as per-candidate deltas.
    candidates = [
        CandidateResult("minimax_early_artifact_creation", delta_in=+7.0, delta_ho=+21.4),
        CandidateResult("qwen_tool_error_middleware", delta_in=+20.9, delta_ho=+14.3),
        CandidateResult("glm5_verification_constraint", delta_in=+9.3, delta_ho=+14.2),
        # A rejected example: trades held-in gain for a held-out loss.
        CandidateResult("hypothetical_overfit_edit", delta_in=+5.0, delta_ho=-2.0),
        # A rejected example: does nothing (no split improves).
        CandidateResult("hypothetical_no_op_edit", delta_in=0.0, delta_ho=0.0),
    ]

    promoted = validate_round(current_pass={}, candidates=candidates)

    for c in candidates:
        verdict = "ACCEPT" if accept(c.delta_in, c.delta_ho) else "reject"
        print(f"{c.candidate_id:35s} delta_in={c.delta_in:+.1f}  delta_ho={c.delta_ho:+.1f}  -> {verdict}")

    print(f"\nPromoted this round: {promoted or '(none — h_(t+1) = h_t)'}")

    # Stochastic-evaluation example: same candidate, repeated noisy runs.
    noisy_in = [+2.0, -1.0, +3.0]
    noisy_ho = [+1.0, +0.5, +2.0]
    print(
        f"\nStochastic candidate mean(delta_in)={mean(noisy_in):+.2f} "
        f"mean(delta_ho)={mean(noisy_ho):+.2f} -> "
        f"{'ACCEPT' if accept_stochastic(noisy_in, noisy_ho) else 'reject'}"
    )
