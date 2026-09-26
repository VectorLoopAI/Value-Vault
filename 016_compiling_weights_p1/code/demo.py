"""
demo.py -- walks through every headline claim named across Part 1 and
Part 2, recomputing what can be recomputed from data_tables.py's raw
numbers via metrics.py's formulas, and printing the paper's own stated
figures alongside for comparison. Run with: python3 demo.py
"""

import data_tables as dt
import metrics as m


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def part1_adoption_gap() -> None:
    section("PART 1 -- the adoption puzzle")
    orch = dt.ADOPTION_GAP["orchestration_frameworks_stars"]
    comp = dt.ADOPTION_GAP["compilation_papers_stars"]
    print(f"Orchestration frameworks: {orch:,}+ combined GitHub stars")
    print(f"Compilation papers:       ~{comp:,} combined GitHub stars")
    print(f"Ratio: {orch / comp:.0f}x more engagement for orchestration "
          f"({dt.ADOPTION_GAP['paper_stated_ratio']})")


def part1_same_model_control() -> None:
    section("PART 1 -- the same-model control (the causal core)")
    wins, ties = 0, 0
    for criterion, row in dt.SAME_MODEL_CONTROL.items():
        outcome = "WIN (p<.001)" if row["significant"] else "tie (n.s.)"
        if row["significant"]:
            wins += 1
        else:
            ties += 1
        print(f"  {criterion:<20} delta={row['delta']:+.2f}  p={row['p']:<6}  {outcome}")
    print(f"\nCompilation wins {wins} of {len(dt.SAME_MODEL_CONTROL)} criteria "
          f"at p<.001, ties on {ties} -- against the exact same weights, same procedure.")


def pct_of_in_context_by_domain() -> None:
    section("Percent of in-context quality, recomputed from the raw tables")

    print("\nTravel (3B), vs. the paper's quoted 82-102% range:")
    for criterion, row in dt.TRAVEL_3B_TABLE.items():
        pct = m.pct_of_in_context(row["sub_3b"], row["in_context"])
        print(f"  {criterion:<20} {row['sub_3b']} / {row['in_context']} = {pct}%")

    print("\nInsurance (8B), vs. the paper's quoted 92-98% range:")
    for criterion, row in dt.INSURANCE_8B_TABLE.items():
        pct = m.pct_of_in_context(row["sub_8b"], row["in_context"])
        print(f"  {criterion:<20} {row['sub_8b']} / {row['in_context']} = {pct}%")


def part2_failure_rates() -> None:
    section("PART 2 -- failure rates: 'eliminated by construction'")
    for domain, row in dt.FAILURE_RATES_PCT.items():
        lg = row.get("langgraph")
        sub = row.get("sub")
        print(f"  {domain:<20} compiled={sub}%   LangGraph orchestrator={lg}%   "
              f"({lg / sub:.1f}x more LangGraph failures)" if sub else "")


def part2_cost_curve() -> None:
    section("PART 2 -- the cost curve that grows with complexity")
    for domain, row in dt.COST_PER_CONVERSATION_TABLE.items():
        recomputed = m.savings_multiplier(row["in_context"], row["subterranean"])
        stated = row["paper_multiple"]
        flag = "" if abs(recomputed - stated) < 0.5 else f"  (recomputed {recomputed}x vs. paper's stated {stated}x -- rounding, see README)"
        print(f"  {domain:<20} in-context=${row['in_context']:<7} sub=${row['subterranean']:<8} "
              f"stated={stated}x{flag}")

    print("\nPer-token self-hosting cost:")
    lo, hi = dt.PER_TOKEN_COST_INPUTS["throughput_tokens_per_sec_range"]
    hourly = dt.PER_TOKEN_COST_INPUTS["a100_hourly_usd"]
    for tps in (lo, hi):
        per_m = m.per_million_token_cost(hourly, tps)
        print(f"  A100 @ ${hourly}/hr, {tps} tok/s -> ${per_m:.4f}/M tokens")
    claude_in = dt.PER_TOKEN_COST_INPUTS["claude_input_per_million_usd"]
    recomputed_multiple = claude_in / m.per_million_token_cost(hourly, lo)
    print(f"  vs. Claude Sonnet 4.5 ${claude_in}/M input -> ~{recomputed_multiple:.0f}x cheaper "
          f"(paper states ~{dt.PER_TOKEN_COST_INPUTS['paper_stated_cheaper_multiple']}x)")

    print("\nBreak-even conversations (compile cost $50-80 vs. travel's per-convo savings):")
    row = dt.COST_PER_CONVERSATION_TABLE["travel_booking"]
    for cost in dt.ONE_TIME_COMPILE_COST_USD["total_range"]:
        be = m.breakeven_conversations(cost, row["in_context"], row["subterranean"])
        print(f"  compile cost ${cost} -> break-even at {be:.0f} conversations "
              f"(paper states within {dt.BREAKEVEN_CONVERSATIONS_STATED})")


def part2_recompile_timeline() -> None:
    section("PART 2 -- the recompile answer")
    t = dt.RECOMPILE_TIMELINE
    print(f"  Data generation:  ~{t['data_generation_convos']} convos, "
          f"{t['data_generation_minutes_concurrent'][0]}-{t['data_generation_minutes_concurrent'][1]} min concurrent")
    print(f"  Fine-tune (8xH200): {t['finetune_8xH200_minutes'][0]}-{t['finetune_8xH200_minutes'][1]} min")
    print(f"  Spot-check:        ~{t['spotcheck_minutes_warm']} min warm")
    print(f"  Fully optimized:   {t['fully_optimized_total_minutes'][0]}-{t['fully_optimized_total_minutes'][1]} min")
    print(f"  Single A100:       {t['single_a100_hours'][0]}-{t['single_a100_hours'][1]} hours")


def part2_honesty_caveats() -> None:
    section("PART 2 -- the two honesty caveats (not smoothed away)")
    ia = dt.INFO_ACCURACY_PLATEAU
    print(f"  Information accuracy plateau: ~{ia['headline_spoken_figure_pct']}% of in-context "
          f"even at 8B ({ia['reading']})")
    jr = dt.JUDGE_ROBUSTNESS
    print(f"  Judge-dependent quality range: {jr['claude_judge_pct_of_in_context_range']} under Claude "
          f"vs. {jr['gpt41_judge_pct_of_in_context_range']} under GPT-4.1")
    print(f"  {jr['caveat']}")

    disc = dt.ZOOM_TRAINING_CONVO_DISCREPANCY
    print(f"\n  Data-provenance note: {disc['convos_per_run']} convos/run x {disc['seeds']} seeds "
          f"= {disc['arithmetic_product']}, but the paper states {disc['paper_stated_total']} total. "
          f"{disc['note']}")


def procedure_graph_demo() -> None:
    section("The paper's F=(N,E,n0,T) formalism, on an illustrative graph")
    import procedure_graph as pg
    g = pg.build_illustrative_example()
    print("(NOT a reconstruction of any real domain in the paper -- see the module docstring.)")
    for scenario_name, scenario in [("customer accepts", {"accepts": True}), ("customer rejects", {"accepts": False})]:
        paths = g.enumerate_acyclic_paths(scenario)
        print(f"\n  scenario: {scenario_name} -> {len(paths)} acyclic path(s)")
        for p in paths:
            print("    " + " -> ".join(p))


if __name__ == "__main__":
    part1_adoption_gap()
    part1_same_model_control()
    pct_of_in_context_by_domain()
    part2_failure_rates()
    part2_cost_curve()
    part2_recompile_timeline()
    part2_honesty_caveats()
    procedure_graph_demo()
    print("\nDone. Every number above traces to backlog/011_compiling_workflows_into_weights.md")
    print("and both episodes' script.md -- see README.md for the exact-vs-computed tagging.")
