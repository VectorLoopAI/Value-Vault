"""
demo.py -- end-to-end toy walkthrough of both loops from the Autodata
episode: the Part 1 inner loop (data acceptance) and the Part 2 outer loop
(harness evolution), using the same acceptance-gate shape at both levels.

Zero external dependencies. Run:

    python3 demo.py
"""

from __future__ import annotations

import random

from acceptance_gate import (
    SolverResult,
    cs_acceptance,
    legal_acceptance,
    HarnessEvolutionGate,
    meta_optimizer_success,
)
from boltzmann_sampler import Candidate, select_parent


def part1_inner_loop_demo() -> None:
    print("=" * 70)
    print("PART 1 -- Agentic Self-Instruct: weak-vs-strong data acceptance")
    print("=" * 70)

    # Round 1: a challenger's first attempt on a paper is usually a
    # high-level summary question -- easy for the weak (4B-class) solver.
    round1_weak = SolverResult(scores=[0.72, 0.68, 0.70])
    round1_strong = SolverResult(scores=[0.80, 0.78, 0.81])
    verdict1 = cs_acceptance(round1_weak, round1_strong)
    print(f"\nRound 1 (summary-style question): {verdict1}")

    # Round 6: judge feedback steered the challenger toward a specific
    # algorithmic step -- weak solver now genuinely struggles.
    round6_weak = SolverResult(scores=[0.40, 0.35, 0.45])
    round6_strong = SolverResult(scores=[0.79, 0.75, 0.80])
    verdict6 = cs_acceptance(round6_weak, round6_strong)
    print(f"Round 6 (algorithmic-step question): {verdict6}")

    # Legal domain: acceptance is a judge verdict pass-through, not a
    # numeric threshold -- because this domain's failure mode is the
    # opposite of CS's (too hard, not too easy).
    legal_judge_verdict = {
        "accept": True,
        "grpo_suitability": "high",
        "reasoning": "weak-rollout scores spread 0.15-0.55 across 5 rollouts, "
                     "not clustered at zero; strong solver reliably correct.",
    }
    print(f"\nLegal domain (judge-verdict pass-through): "
          f"{legal_acceptance(legal_judge_verdict)}")


def part2_outer_loop_demo() -> None:
    print("\n" + "=" * 70)
    print("PART 2 -- meta-optimization: the same gate, one level up")
    print("=" * 70)

    rng = random.Random(7)

    # A tiny population of harness-prompt candidates with running-average
    # validation scores (as if several iterations have already run).
    population = [
        Candidate("baseline", prompt="baseline_prompt_v0", score=0.621),
        Candidate("mutant_leak_fix", prompt="baseline_prompt_v0+leak_check", score=0.681),
        Candidate("mutant_pos_weights", prompt="baseline_prompt_v0+positive_only_rubric", score=0.774),
    ]
    parent = select_parent(population, temperature=0.1, rng=rng)
    print(f"\nBoltzmann-selected parent for this iteration: "
          f"{parent.id} (score={parent.score:.3f})")

    # The harness-evolution gate: does the newly proposed mutant strictly
    # beat the parent it was mutated from?
    gate = HarnessEvolutionGate(current_prompt=parent.prompt, current_score=parent.score)

    # A validation-set pass rate is computed by running the candidate over
    # many papers and checking meta_optimizer_success() on each -- here we
    # fake two papers' worth of solver results for illustration.
    paper_a_pass = meta_optimizer_success(
        weak=SolverResult(scores=[0.55, 0.60, 0.50]),
        strong=SolverResult(scores=[0.85, 0.88, 0.82]),
    )
    paper_b_pass = meta_optimizer_success(
        weak=SolverResult(scores=[0.70, 0.72, 0.68]),   # too easy -- weak solver over 0.65
        strong=SolverResult(scores=[0.90, 0.91, 0.89]),
    )
    candidate_val_score = sum([paper_a_pass, paper_b_pass]) / 2
    print(f"Mutant's validation pass rate on this minibatch: {candidate_val_score:.3f} "
          f"(paper_a={paper_a_pass}, paper_b={paper_b_pass})")

    result = gate.evaluate(
        candidate_prompt="baseline_prompt_v0+leak_check+stricter_gap_test",
        candidate_score=candidate_val_score,
        diff_description="added a paper-specific-insight self-test to the challenger prompt",
        iteration=125,
    )
    print(f"Harness-evolution gate verdict: {result}")


if __name__ == "__main__":
    part1_inner_loop_demo()
    part2_outer_loop_demo()
