"""
reward.py — Reference implementation of the Harness-1 terminal-only reward function.

Reproduces the reward decomposition described in the paper and walked in the video
(SEG 17): empty curated set short-circuits to pi_empty; otherwise the reward blends an
F-beta set-quality term (beta=2, weights recall ~4x precision), trajectory coverage, an
answer-evidence shaping term, an answer-miss penalty (found the answer evidence but
failed to promote it — "discovery vs. selection", SEG 32), a tool-diversity bonus
(target nu0=6), and a turn penalty. "The reward separates discovery from selection."

This is the harness-side scoring function only. It assumes you already have, per rollout:
  curated                  set of doc_ids the policy kept in C_t at episode end
  gold                      set of doc_ids that are actually relevant (benchmark labels)
  trajectory_seen           set of doc_ids the trajectory encountered at any point
  answer_evidence_found     bool — did the trajectory ever see the evidence needed to answer
  answer_evidence_promoted  bool — did that evidence make it into the final curated set
  distinct_tools_used       int
  num_turns                 int

NOTE on which numbers are the paper's vs. illustrative: pi_empty, f_beta (beta), the
diversity target nu0, and turn_cap are all published constants (see
../configs/harness_config.yaml). The relative weights combining the reward's sub-terms
(set_quality_weight, coverage_weight, etc.) are NOT published anywhere in the source
material — they're marked "(illustrative default)" in the config and exist only so this
reference implementation runs end to end. Tune them for your own reward surface.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RolloutOutcome:
    curated: set
    gold: set
    trajectory_seen: set
    answer_evidence_found: bool
    answer_evidence_promoted: bool
    distinct_tools_used: int
    num_turns: int


def f_beta(curated: set, gold: set, beta: float) -> float:
    if not curated or not gold:
        return 0.0
    tp = len(curated & gold)
    precision = tp / len(curated)
    recall = tp / len(gold)
    if precision == 0.0 and recall == 0.0:
        return 0.0
    b2 = beta ** 2
    return (1 + b2) * precision * recall / (b2 * precision + recall + 1e-9)


def compute_reward(outcome: RolloutOutcome, cfg: dict) -> dict:
    rcfg = cfg["reward"]

    if not outcome.curated:
        # empty curated set -> short-circuit, done (SEG 17)
        return {"reward": rcfg["pi_empty"], "breakdown": {"empty_set_shortcircuit": rcfg["pi_empty"]}}

    set_quality = f_beta(outcome.curated, outcome.gold, beta=rcfg["f_beta"])
    coverage = len(outcome.trajectory_seen & outcome.gold) / max(1, len(outcome.gold))

    answer_evidence_term = 0.0
    answer_miss_penalty = 0.0
    if outcome.answer_evidence_found:
        if outcome.answer_evidence_promoted:
            answer_evidence_term = rcfg["answer_evidence_weight"]
        else:
            # found the evidence but failed to promote it into the final set — the
            # "selection gap, not a discovery gap" penalty (SEG 32)
            answer_miss_penalty = -rcfg["answer_miss_penalty"]

    diversity_bonus = rcfg["diversity_weight"] * min(
        1.0, outcome.distinct_tools_used / rcfg["diversity_target_nu0"]
    )
    turn_penalty = -rcfg["turn_penalty_weight"] * (outcome.num_turns / rcfg["turn_cap"])

    total = (
        rcfg["set_quality_weight"] * set_quality
        + rcfg["coverage_weight"] * coverage
        + answer_evidence_term
        + answer_miss_penalty
        + diversity_bonus
        + turn_penalty
    )

    return {
        "reward": total,
        "breakdown": {
            "set_quality_fbeta": set_quality,
            "trajectory_coverage": coverage,
            "answer_evidence_term": answer_evidence_term,
            "answer_miss_penalty": answer_miss_penalty,
            "tool_diversity_bonus": diversity_bonus,
            "turn_penalty": turn_penalty,
        },
    }
