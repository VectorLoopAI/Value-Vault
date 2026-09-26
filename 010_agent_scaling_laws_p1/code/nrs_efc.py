"""
nrs_efc.py — NRS-EFC (non-redundant stable EFC): three deterministic gates
layered on top of Estimated-EFC for messy real execution traces (§3.3,
Part 2 SEG 05-06).

EFC_hat_t^nr = (EFC_hat_t * Q_t * G_t^nr * Lambda_t^nr) / (1 + alpha_A * A_t)

Only two numeric points in the source paper's appendix survive its OCR
damage clean: the endpoints of the status-quality score (Q_t: 1.00 for a
passed check, 0.00 for an API error) and the repair-event loop-gate
contrast (Lambda_t: 0.95 status-aware -> 0.45 under NRS). Everything else
marked (illustrative) below is a placeholder — replace it with your own
calibration; do not treat the middle Q_t bands as paper-verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass

ALPHA_A = 0.35  # ambiguity-penalty coefficient — fixed across every experiment (paper)

# status_quality: paper-verbatim only at the two endpoints (see docstring / README)
STATUS_QUALITY = {
    "passed": 1.00,  # (paper) — a checker/test that actually passed
    "assertion_error": 0.70,  # (illustrative — OCR-damaged in source)
    "runtime_error": 0.55,  # (illustrative — OCR-damaged in source)
    "timeout": 0.40,  # (illustrative — OCR-damaged in source)
    "static_reject": 0.20,  # (illustrative — OCR-damaged in source)
    "api_error": 0.00,  # (paper) — infrastructure noise, not task signal
}


def ambiguity_penalty(attempt_index: int, alpha_a: float = ALPHA_A) -> float:
    """1 + alpha_A * A_t — grows with the attempt index, so repeated tries
    on the same subgoal get taxed harder each time."""
    return 1.0 + alpha_a * attempt_index


@dataclass(frozen=True)
class NRSGates:
    status: str  # key into STATUS_QUALITY
    progress_gate: float  # G_t^nr in [0, 1]
    loop_gate: float  # Lambda_t^nr in [0, 1] — e.g. 0.45 for a repeated repair event
    attempt_index: int  # A_t — which retry number this is on the active subgoal

    @property
    def status_quality(self) -> float:
        return STATUS_QUALITY[self.status]


def nrs_efc(estimated_efc_t: float, gates: NRSGates) -> float:
    """EFC_hat_t^nr = (EFC_hat_t * Q_t * G_t^nr * Lambda_t^nr) / (1 + alpha_A * A_t)"""
    numerator = estimated_efc_t * gates.status_quality * gates.progress_gate * gates.loop_gate
    return numerator / ambiguity_penalty(gates.attempt_index)


if __name__ == "__main__":
    # The repair-event example from Part 2 (SEG 06): the identical event,
    # scored twice — once with status-aware loop credit (0.95), once with
    # the NRS redundancy tax applied after a repeat (0.45).
    base_efc = 4.0  # arbitrary Estimated-EFC_t for this event
    first_attempt = NRSGates(status="passed", progress_gate=0.9, loop_gate=0.95, attempt_index=0)
    repeated_attempt = NRSGates(status="passed", progress_gate=0.9, loop_gate=0.45, attempt_index=3)
    print(f"first attempt -> NRS-EFC_t = {nrs_efc(base_efc, first_attempt):.3f}")
    print(f"repeated fix  -> NRS-EFC_t = {nrs_efc(base_efc, repeated_attempt):.3f}")
