"""
reward.py — Reference implementation of the "From Trainee to Trainer" RL reward
(paper §3.1.2 / SEG 07). Wired to exactly the published constants in
../configs/reward_config.yaml.

    R = w_acc * R_acc + w_len * R_len

R_acc:
    Gated by eight strict validity checks (Parsable, Legal-move, Conflict-free,
    Goal-reached, Start-correct, Agent-count, Hole-free, In-bounds). Fail any one and
    R_acc = 0 outright. If all eight pass, R_acc is shaped by the cost gap to the
    ground-truth solution:
        c = model_cost - gt_cost
        c_max = 2 * gt_cost
        R_acc(c) = 1.0                      if c == 0
                 = 1.0 - 0.7 * (c / c_max)    if 0 < c <= c_max
                 = 0.3                        if c > c_max
    Falls back to 0.5 if the ground-truth cost can't be parsed.

R_len:
    Discourages verbose responses via a soft threshold L1=1500 and a hard threshold
    L2=4096 (measured in tokens):
        R_len = 0                              if len(response) <= L1
              = -(len - L1) / (L2 - L1)          if L1 < len < L2
              = -1                                if len >= L2

Adaptive weights (w_acc, w_len):
    Shift emphasis from brevity to correctness as the model learns concision, driven
    by r = EMA of the short-response ratio (fraction of responses with len <= L1):
        (w_acc, w_len) = (0.5, 0.5)                 if r < 0.5
                        = lerp((0.5,0.5),(0.8,0.2))   if 0.5 <= r < 0.9
                        = (0.8, 0.2)                   if r >= 0.9

Run this file directly for a self-contained sanity check against a handful of
worked examples.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VALIDITY_CHECKS = (
    "Parsable",
    "Legal-move",
    "Conflict-free",
    "Goal-reached",
    "Start-correct",
    "Agent-count",
    "Hole-free",
    "In-bounds",
)


@dataclass
class RewardConfig:
    cost_gap_multiplier: float = 2.0
    reward_at_zero_gap: float = 1.0
    reward_floor_saturated: float = 0.3
    shaping_slope: float = 0.7
    unparseable_gt_fallback: float = 0.5

    soft_threshold_L1: int = 1500
    hard_threshold_L2: int = 4096

    r_low: float = 0.5
    r_high: float = 0.9
    weights_low: tuple = (0.5, 0.5)     # (w_acc, w_len)
    weights_high: tuple = (0.8, 0.2)


@dataclass
class Rollout:
    validity: dict            # {check_name: bool} for all VALIDITY_CHECKS
    model_cost: float | None  # None if unparseable
    gt_cost: float | None     # None if the ground-truth cost itself can't be parsed
    response_len_tokens: int


def accuracy_reward(rollout: Rollout, cfg: RewardConfig) -> float:
    """R_acc — validity-gated, cost-shaped."""
    if not all(rollout.validity.get(check, False) for check in VALIDITY_CHECKS):
        return 0.0

    if rollout.gt_cost is None or rollout.model_cost is None:
        return cfg.unparseable_gt_fallback

    c = rollout.model_cost - rollout.gt_cost
    if c <= 0:
        return cfg.reward_at_zero_gap

    c_max = cfg.cost_gap_multiplier * rollout.gt_cost
    if c_max <= 0:
        return cfg.reward_floor_saturated

    if c <= c_max:
        return cfg.reward_at_zero_gap - cfg.shaping_slope * (c / c_max)

    return cfg.reward_floor_saturated


def length_reward(rollout: Rollout, cfg: RewardConfig) -> float:
    """R_len — soft/hard token-length penalty."""
    length = rollout.response_len_tokens
    l1, l2 = cfg.soft_threshold_L1, cfg.hard_threshold_L2
    if length <= l1:
        return 0.0
    if length >= l2:
        return -1.0
    return -(length - l1) / (l2 - l1)


def adaptive_weights(short_response_ema: float, cfg: RewardConfig) -> tuple[float, float]:
    """(w_acc, w_len), interpolated by the EMA short-response ratio r."""
    r = short_response_ema
    if r < cfg.r_low:
        return cfg.weights_low
    if r >= cfg.r_high:
        return cfg.weights_high

    t = (r - cfg.r_low) / (cfg.r_high - cfg.r_low)
    w_acc = cfg.weights_low[0] + t * (cfg.weights_high[0] - cfg.weights_low[0])
    w_len = cfg.weights_low[1] + t * (cfg.weights_high[1] - cfg.weights_low[1])
    return (w_acc, w_len)


def total_reward(rollout: Rollout, short_response_ema: float, cfg: RewardConfig | None = None) -> dict:
    cfg = cfg or RewardConfig()
    r_acc = accuracy_reward(rollout, cfg)
    r_len = length_reward(rollout, cfg)
    w_acc, w_len = adaptive_weights(short_response_ema, cfg)
    total = w_acc * r_acc + w_len * r_len
    return {
        "reward": total,
        "R_acc": r_acc,
        "R_len": r_len,
        "w_acc": w_acc,
        "w_len": w_len,
    }


if __name__ == "__main__":
    cfg = RewardConfig()
    all_valid = {check: True for check in VALIDITY_CHECKS}
    one_broken = dict(all_valid, **{"Conflict-free": False})

    cases = [
        ("perfect plan, early training (r=0.2)",
         Rollout(all_valid, model_cost=10, gt_cost=10, response_len_tokens=800), 0.2),
        ("plan costs 1.5x ground truth, mid-shift (r=0.7)",
         Rollout(all_valid, model_cost=15, gt_cost=10, response_len_tokens=1200), 0.7),
        ("plan costs 3x ground truth (saturates at 0.3), late training (r=0.95)",
         Rollout(all_valid, model_cost=30, gt_cost=10, response_len_tokens=3000), 0.95),
        ("fails a validity gate -> R_acc=0 regardless of cost",
         Rollout(one_broken, model_cost=10, gt_cost=10, response_len_tokens=500), 0.5),
        ("valid, verbose past the hard cap -> R_len=-1",
         Rollout(all_valid, model_cost=10, gt_cost=10, response_len_tokens=5000), 0.5),
    ]

    for label, rollout, r_ema in cases:
        result = total_reward(rollout, r_ema, cfg)
        print(f"{label}\n  -> {result}\n")
