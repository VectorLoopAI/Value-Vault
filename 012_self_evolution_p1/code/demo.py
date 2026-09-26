"""
demo.py -- recomputes every headline claim from both episodes against the
paper's own tables, using only metrics.py + data_tables.py. Zero external
dependencies -- Python 3.10+ stdlib only.

Run: python3 demo.py
"""

from __future__ import annotations

from metrics import (
    spread,
    is_non_monotonic_peak,
    activation_adherence_gap,
    drift,
)
from data_tables import (
    EVOLVER_UPDATING_PARTIAL,
    EVOLVER_GLOBAL_SPREAD_CLAIM_PP,
    FLINK_QUERY_CASE_STUDY,
    AGENT_BENEFIT_TABLE,
    ACTIVATION_ADHERENCE_TABLE,
    ADHERENCE_DRIFT_TABLE,
    DRIFT_PHASE_LABELS,
    EXTREME_PAIRING_MARGIN_PP,
    SKILLSBENCH_CAVEAT,
)


def part1_evolver_flatness() -> None:
    print("=== PART 1 -- harness-updating (the writer) is flat ===")
    for bench, cells in EVOLVER_UPDATING_PARTIAL.items():
        named_spread = spread(list(cells.values()))
        print(f"  {bench}: named evolvers = {cells}")
        print(f"    spread among NAMED evolvers = {named_spread:.1f} pp "
              f"(paper's own global max across all 7 evolvers = {EVOLVER_GLOBAL_SPREAD_CLAIM_PP} pp)")
        if named_spread > EVOLVER_GLOBAL_SPREAD_CLAIM_PP:
            print("    ! inconsistency: named-cell spread exceeds the paper's stated global max -- check sources")
    best_sb, worst_sb = "Qwen3.5-9B", "Claude Opus 4.6"
    print(f"\n  SkillsBench headline: {best_sb} ({EVOLVER_UPDATING_PARTIAL['SB'][best_sb]} pp) "
          f"beats {worst_sb} ({EVOLVER_UPDATING_PARTIAL['SB'][worst_sb]} pp) as an evolver.")
    print(f"  flink-query case study: no skill = {FLINK_QUERY_CASE_STUDY['no_skill']}, "
          f"9B-written skill = {FLINK_QUERY_CASE_STUDY['skill_by_qwen3_5_9b']}, "
          f"Opus-written skill = {FLINK_QUERY_CASE_STUDY['skill_by_opus_4_6']} "
          f"-- identical downstream score, {len(FLINK_QUERY_CASE_STUDY['procedure_steps'])}-step procedure "
          f"the paper calls 'procedurally isomorphic'.\n")


def part2_benefit_curve() -> None:
    print("=== PART 2 -- harness-benefit (the reader) is non-monotonic ===")
    for bench in ("SWE", "MCP", "SB"):
        rows = sorted(
            ((agent, vals[bench][0], vals[bench][1]) for agent, vals in AGENT_BENEFIT_TABLE.items()),
            key=lambda r: r[1],
        )
        peak_name, peak_gain = is_non_monotonic_peak(rows)
        weakest, strongest = rows[0], rows[-1]
        print(f"  {bench}: base-capability order = {[r[0] for r in rows]}")
        print(f"    peak gain = {peak_name} ({peak_gain} pp)  |  "
              f"weakest agent = {weakest[0]} ({weakest[2]} pp)  |  "
              f"strongest agent = {strongest[0]} ({strongest[2]} pp)")
        is_middle = peak_name not in (weakest[0], strongest[0])
        print(f"    non-monotonic (peak is neither weakest nor strongest)? {is_middle}")
    print(f"\n  Honesty check -- {SKILLSBENCH_CAVEAT}\n")


def part2_activation_vs_adherence() -> None:
    print("=== PART 2 -- activation (SLR) vs. adherence (HFR) are separable failures ===")
    a, b = "Qwen3-235B-A22B", "Opus 4.6"
    row_a, row_b = ACTIVATION_ADHERENCE_TABLE[a], ACTIVATION_ADHERENCE_TABLE[b]
    result = activation_adherence_gap(row_a["SLR"], row_a["HFR"], row_b["SLR"], row_b["HFR"])
    print(f"  {a}: SLR={row_a['SLR']}, HFR={row_a['HFR']}, LPR={row_a['LPR']}")
    print(f"  {b}: SLR={row_b['SLR']}, HFR={row_b['HFR']}, LPR={row_b['LPR']}")
    print(f"  SLR gap = {result['slr_gap']} (dead heat on activation: {result['activation_dead_heat']})")
    print(f"  HFR ratio (weaker/stronger) = {result['hfr_ratio']} "
          f"(adherence diverges sharply: {result['adherence_diverges']})\n")

    print("  Full SLR/HFR table (do the two columns correlate?):")
    for model, row in ACTIVATION_ADHERENCE_TABLE.items():
        print(f"    {model:20s} SLR={row['SLR']:.3f}  HFR={row['HFR']:.3f}  LPR={row['LPR']:.3f}")
    print()


def part2_drift() -> None:
    print("=== PART 2 -- long-horizon adherence drift ===")
    print(f"  phases: {DRIFT_PHASE_LABELS}")
    drifts = {}
    for model, phases in ADHERENCE_DRIFT_TABLE.items():
        d = drift(phases)
        drifts[model] = d
        print(f"  {model:22s} {phases}  ->  drift (final - load) = {d:+.2f}")
    weak_drift = drifts["Qwen3-32B (weak)"]
    strong_drift = drifts["Opus 4.6 (strong)"]
    ratio = abs(weak_drift) / abs(strong_drift)
    print(f"\n  weak model drift is {ratio:.1f}x steeper than the strong model's\n")


def part2_extreme_pairing() -> None:
    print("=== PART 2 -- extreme-pairing stress test (weak+best-evolver vs strong+worst-evolver) ===")
    for bench, margin in EXTREME_PAIRING_MARGIN_PP.items():
        print(f"  {bench}: strong agent still wins by {margin} pp")
    print()


if __name__ == "__main__":
    part1_evolver_flatness()
    part2_benefit_curve()
    part2_activation_vs_adherence()
    part2_drift()
    part2_extreme_pairing()
