"""
advantage.py — the two-level advantage estimator from AdaCoM §3.2.

Outcome reward (sparse, trajectory-level) and process reward (dense,
step-level) are normalized *separately* before being combined — this is
what keeps the step-level signal alive even when every rollout in a GRPO
group gets the same outcome reward (paper): "When sigma_R = 0, ... the
task-level term vanishes, and the step-level term provides the only
learning signal within such same-outcome groups."
"""

from __future__ import annotations

import statistics


def _mean_std(values: list, eps: float) -> tuple:
    if not values:
        return 0.0, eps
    mean = statistics.fmean(values)
    std = statistics.pstdev(values) if len(values) > 1 else 0.0
    return mean, std


def task_level_advantage(outcome_rewards: list, eps: float = 1e-6) -> list:
    """One outcome reward R_i per rollout in the group -> one normalized
    advantage A_i^R per rollout (paper: A_i^R = (R_i - mu_R) / (sigma_R + eps))."""
    mean, std = _mean_std(outcome_rewards, eps)
    return [(r - mean) / (std + eps) for r in outcome_rewards]


def step_level_advantage(process_rewards_per_rollout: list, eps: float = 1e-6) -> list:
    """Process reward Q_{i,t} normalized over *all* steps across the whole
    group (paper: A_{i,t}^Q = (Q_{i,t} - mu_Q) / (sigma_Q + eps))."""
    flat = [q for rollout in process_rewards_per_rollout for q in rollout]
    mean, std = _mean_std(flat, eps)
    return [[(q - mean) / (std + eps) for q in rollout] for rollout in process_rewards_per_rollout]


def combine_advantages(
    outcome_rewards: list,
    process_rewards_per_rollout: list,
    alpha: float = 0.1,
    eps: float = 1e-6,
) -> list:
    """Broadcast each rollout's task-level advantage to every one of its
    steps, add alpha times the step-level advantage, then renormalize the
    combined value over the whole group (paper §3.2)."""
    task_adv = task_level_advantage(outcome_rewards, eps)
    step_adv = step_level_advantage(process_rewards_per_rollout, eps)

    raw = []
    for i, rollout_steps in enumerate(process_rewards_per_rollout):
        raw.append([task_adv[i] + alpha * step_adv[i][t] for t in range(len(rollout_steps))])

    flat_raw = [a for rollout in raw for a in rollout]
    mean, std = _mean_std(flat_raw, eps)
    return [[(a - mean) / (std + eps) for a in rollout] for rollout in raw]
