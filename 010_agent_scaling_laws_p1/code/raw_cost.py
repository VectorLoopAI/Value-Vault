"""
raw_cost.py — C_raw(tau), the raw-expenditure baseline behind the paper's
matched-budget intervention (§3.4, §4.2). Weights are fixed across every
experiment; this is the yardstick EFC is measured against, not a
replacement for it — the whole point of the matched-budget intervention
(Part 1) is holding *this* number constant while changing feedback
quality, and watching success move anyway.
"""

from __future__ import annotations

from dataclasses import dataclass

U_TOK = 1000.0  # token unit (paper)
LAMBDA_TOK = 1.0  # per-1000-token weight (paper)
LAMBDA_TOOL = 0.35  # per tool call (paper)
LAMBDA_TIME = 0.10  # per wall-clock unit (paper)
LAMBDA_OP = 0.04  # per operation (paper)


@dataclass(frozen=True)
class RunSpend:
    n_tokens: float
    n_tool_calls: float
    wall_time: float
    n_ops: float

    @property
    def raw_cost(self) -> float:
        """C_raw = lambda_tok*(N_tok/U_tok) + lambda_tool*N_tool
        + lambda_time*T_wall + lambda_op*N_op"""
        return (
            LAMBDA_TOK * (self.n_tokens / U_TOK)
            + LAMBDA_TOOL * self.n_tool_calls
            + LAMBDA_TIME * self.wall_time
            + LAMBDA_OP * self.n_ops
        )


def raw_cost_delta_pct(a: RunSpend, b: RunSpend) -> float:
    """Mean absolute raw-cost delta, as a percentage — this is the number
    the paper drives to 0.000% in its matched-budget intervention (Part 1,
    SEG 15): two conditions with identical token/tool-call/wall-clock
    budgets, verified rather than assumed."""
    base = max(a.raw_cost, 1e-9)
    return abs(a.raw_cost - b.raw_cost) / base * 100.0


if __name__ == "__main__":
    low_quality = RunSpend(n_tokens=38000, n_tool_calls=22, wall_time=190, n_ops=9)
    high_quality = RunSpend(n_tokens=38000, n_tool_calls=22, wall_time=190, n_ops=9)
    print(f"low-quality condition  C_raw = {low_quality.raw_cost:.3f}")
    print(f"high-quality condition C_raw = {high_quality.raw_cost:.3f}")
    print(f"raw-cost delta = {raw_cost_delta_pct(low_quality, high_quality):.3f}%  (paper reports 0.000%)")
