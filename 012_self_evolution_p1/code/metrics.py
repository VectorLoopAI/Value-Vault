"""
metrics.py -- the harness-updating / harness-benefit decomposition (paper
Section 3.3 of "Harness Updating Is Not Harness Benefit: Disentangling
Evolution Capabilities in Self-Evolving LLM Agents", arXiv:2605.30621v1).

Four formulas, reproduced exactly:

    M_base(f)          = J_X(f, H_0)
    Delta(f, e)         = J_X(f, H_T^(f,e)) - M_base(f)
    Delta_update(e)      = mean over f in F* of Delta(f, e)      -- isolates the WRITER
    Delta_benefit(f)     = max  over e in E* of Delta(f, e)      -- isolates the READER

This module takes the *already-scored* base/evolved numbers (there's no
public eval harness to re-run -- see the README's note on the paper's
placeholder repo link) and lets you recompute the decomposition and its
headline claims from the raw numbers, rather than trusting either video's
narration.
"""

from __future__ import annotations


def pairwise_gain(base_capability: float, evolved_score: float) -> float:
    """Delta(f, e) for one specific agent-evolver pairing."""
    return evolved_score - base_capability


def harness_updating_capability(pairwise_gains: list[float]) -> float:
    """Delta_update(e): mean of an evolver's gains across the fixed anchor
    AGENT set F* -- holds the reader side constant, isolates the writer."""
    if not pairwise_gains:
        raise ValueError("need at least one anchor-agent gain")
    return sum(pairwise_gains) / len(pairwise_gains)


def harness_benefit_capability(pairwise_gains: list[float]) -> float:
    """Delta_benefit(f): max of an agent's gains across the fixed anchor
    EVOLVER set E* -- holds the writer side constant, isolates the reader."""
    if not pairwise_gains:
        raise ValueError("need at least one anchor-evolver gain")
    return max(pairwise_gains)


def spread(values: list[float]) -> float:
    """Best-minus-worst gap -- the flatness statistic used throughout Part 1
    ("at most 3.1 percentage points between best and worst evolver")."""
    return max(values) - min(values)


def is_non_monotonic_peak(sorted_by_base: list[tuple[str, float, float]]) -> tuple[str, float]:
    """Given (name, base_capability, gain) sorted by ascending base
    capability, return the (name, gain) of whoever has the single largest
    gain. A peak that lands neither at index 0 (weakest) nor index -1
    (strongest) is the non-monotonic "inverted U" Part 2 argues for.
    """
    if not sorted_by_base:
        raise ValueError("need at least one agent")
    peak = max(sorted_by_base, key=lambda row: row[2])
    return peak[0], peak[2]


def activation_adherence_gap(slr_a: float, hfr_a: float, slr_b: float, hfr_b: float,
                              slr_tolerance: float = 0.02) -> dict:
    """The Part 2 mechanism cell: compares two models' skill-load rate (SLR)
    and harness-following rate (HFR). Returns whether they're a "dead heat"
    on activation (SLR within tolerance) while diverging sharply on
    adherence (HFR ratio) -- the signature of an adherence, not activation,
    failure.
    """
    slr_gap = abs(slr_a - slr_b)
    hfr_ratio = min(hfr_a, hfr_b) / max(hfr_a, hfr_b) if max(hfr_a, hfr_b) else 0.0
    return {
        "slr_gap": round(slr_gap, 4),
        "activation_dead_heat": slr_gap <= slr_tolerance,
        "hfr_ratio": round(hfr_ratio, 4),
        "adherence_diverges": hfr_ratio < 0.6,   # weaker model follows <60% as often
    }


def drift(phase_scores: list[float]) -> float:
    """Adherence drift: load-time adherence minus final-turn adherence.
    Negative = adherence decayed over the trajectory (Part 2's "long-horizon
    instruction-following bottleneck")."""
    if len(phase_scores) < 2:
        raise ValueError("need at least a load-time and a final-turn score")
    return phase_scores[-1] - phase_scores[0]
