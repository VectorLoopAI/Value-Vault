"""
estimated_efc.py — Estimated-EFC: predicting the oracle-defined event
target from trace-observable features alone, with no hidden task state
(§3.3; explained on-screen in Part 2, SEG 03: "the Estimated-EFC part one
kept naming and never explained").

Nine features, verbatim from the source note's phi(e_t):
  c_t     — whether a checker fired
  h_t     — checker scope
  z_t     — whether a later step referenced this tool result
  p_t     — whether the plan changed
  m_t     — whether memory retained it
  a_t     — whether a repeated error was avoided
  q_t     — observation consistency
  delta_t — subgoal progress
  rho_t   — trace position

theta (the calibrated weight vector) is NOT published by the paper — it is
fit on a held-out calibration split and frozen before evaluation (§3.3).
DEFAULT_THETA below is an illustrative placeholder so this module runs
out of the box; replace it by fitting on your own labeled calibration
traces before trusting the output (see README).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

FEATURE_NAMES = ("c_t", "h_t", "z_t", "p_t", "m_t", "a_t", "q_t", "delta_t", "rho_t")

# illustrative only — the paper does not publish these weights (see docstring)
DEFAULT_THETA0 = -1.0
DEFAULT_THETA = {
    "c_t": 0.9,
    "h_t": 0.3,
    "z_t": 0.6,
    "p_t": 0.5,
    "m_t": 0.8,
    "a_t": 0.4,
    "q_t": 0.3,
    "delta_t": 0.5,
    "rho_t": -0.1,
}


@dataclass(frozen=True)
class TraceFeatures:
    c_t: float
    h_t: float
    z_t: float
    p_t: float
    m_t: float
    a_t: float
    q_t: float
    delta_t: float
    rho_t: float

    def as_dict(self) -> dict:
        return {name: getattr(self, name) for name in FEATURE_NAMES}


def estimated_efc(phi: TraceFeatures, theta0: float = DEFAULT_THETA0, theta: dict | None = None) -> float:
    """EFC_hat_t = max(0, exp(theta0 + theta . phi(e_t)) - 1)

    Discipline rule (§3.3, Part 2 SEG 04): the binary task outcome is used
    only as the response variable when *evaluating* this estimator — never
    wire a success/fail label into phi or theta here. The max(0, ...) floor
    means an event that clears nothing earns nothing, the same bottleneck
    behavior the oracle version has, rebuilt from the outside."""
    theta = theta or DEFAULT_THETA
    linear = theta0 + sum(theta[name] * getattr(phi, name) for name in FEATURE_NAMES)
    return max(0.0, math.exp(linear) - 1.0)


if __name__ == "__main__":
    checker_backed_event = TraceFeatures(
        c_t=1.0, h_t=0.8, z_t=1.0, p_t=1.0, m_t=1.0, a_t=1.0, q_t=0.9, delta_t=0.9, rho_t=0.4
    )
    unchecked_critique = TraceFeatures(
        c_t=0.0, h_t=0.0, z_t=0.1, p_t=0.0, m_t=0.0, a_t=0.0, q_t=0.3, delta_t=0.1, rho_t=0.4
    )
    print(f"checker-backed event -> EFC_hat_t = {estimated_efc(checker_backed_event):.3f}")
    print(f"unchecked critique    -> EFC_hat_t = {estimated_efc(unchecked_critique):.3f}")
