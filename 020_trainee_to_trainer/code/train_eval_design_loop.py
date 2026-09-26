"""
train_eval_design_loop.py — Reference skeleton of Algorithm 1, the train -> eval ->
design loop from "From Trainee to Trainer" (paper §3.2 / SEG 08), with a runnable,
dependency-free implementation of the one piece of the loop that's fully specified and
mechanical: projecting a proposed config back onto the valid constraint space.

Each round:
    1. Generate the environment/training set D_t from the current config omega_t.
    2. GRPO-update the policy on D_t.
    3. Validate on the frozen held-out validation set.
    4. Append {config, validation_result} to history.
    5. Compose context from the selected modules (see ../configs/context_modules.yaml
       and ../system_prompts/environment_engineer_prompt.md) -- V6 = F + G +
       H_without_default + T.
    6. The policy (the *current checkpoint itself*, not a separate model) proposes
       omega_tilde_{t+1}.
    7. Project omega_tilde_{t+1} back onto the valid constraint space -> omega_{t+1}.

Steps 1-2-3-6 need a real generator, a real trainer, and a real LLM call, so they're
left as clearly-marked stubs here (`generate_environment`, `grpo_update`, `validate`,
`propose_next_config` — wire these to your own stack). Step 7, the constraint
projection, is fully specified by the generator's own definition (data ratios sum to 1
per map size, hole/wait ratios in [0,1]) and is implemented below end to end.

Run this file directly to see the projection step applied to a deliberately
mis-normalized model proposal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

MAP_SIZES = ["3x3", "4x4", "5x5", "6x6", "7x7", "8x8", "9x9", "10x10"]


@dataclass
class SizeConfig:
    data_ratio: float
    hole_ratio: float
    wait_ratio: float


EnvConfig = dict[str, SizeConfig]   # map_size -> SizeConfig


def project_config(proposed: EnvConfig) -> EnvConfig:
    """
    Project a (possibly invalid) proposed config onto the valid constraint space:
      - hole_ratio, wait_ratio: clipped independently, per size, to [0, 1]
      - data_ratio: clipped to [0, 1] per size, then renormalized across all sizes
        so they sum to exactly 1 (simplex projection by simple rescaling -- the
        generator's own constraint is "sums to 1 across sizes", nothing fancier is
        specified in the source material, so a rescale is the faithful minimal
        projection).
    """
    clipped = {
        size: SizeConfig(
            data_ratio=min(1.0, max(0.0, cfg.data_ratio)),
            hole_ratio=min(1.0, max(0.0, cfg.hole_ratio)),
            wait_ratio=min(1.0, max(0.0, cfg.wait_ratio)),
        )
        for size, cfg in proposed.items()
    }

    total_data_ratio = sum(cfg.data_ratio for cfg in clipped.values())
    if total_data_ratio <= 0:
        # degenerate proposal (e.g. all zeros) -> fall back to uniform
        n = len(clipped)
        for cfg in clipped.values():
            cfg.data_ratio = 1.0 / n
        return clipped

    for cfg in clipped.values():
        cfg.data_ratio = cfg.data_ratio / total_data_ratio

    return clipped


@dataclass
class RoundResult:
    round_index: int
    config: EnvConfig
    validation: dict           # {"valid_rate": float, "optimal_rate": float, "per_size": {...}}


@dataclass
class Loop:
    """Orchestrates the train -> eval -> design loop. Wire the four Callables to your
    own generator / trainer / evaluator / policy-as-engineer call."""

    generate_environment: Callable[[EnvConfig], object]     # omega_t -> D_t
    grpo_update: Callable[[object], None]                    # policy.update(D_t)
    validate: Callable[[], dict]                              # -> validation result dict
    propose_next_config: Callable[[list[RoundResult]], EnvConfig]  # context -> omega_tilde_{t+1}

    history: list[RoundResult] = field(default_factory=list)

    def run_round(self, round_index: int, config: EnvConfig) -> RoundResult:
        training_data = self.generate_environment(config)      # step 1
        self.grpo_update(training_data)                          # step 2
        validation = self.validate()                              # step 3
        result = RoundResult(round_index, config, validation)
        self.history.append(result)                                # step 4
        return result

    def design_next_round(self) -> EnvConfig:
        # step 5 (compose context from self.history) happens inside
        # propose_next_config -- see ../system_prompts/environment_engineer_prompt.md
        # for what V6's context assembly looks like.
        proposed = self.propose_next_config(self.history)          # step 6
        return project_config(proposed)                              # step 7


if __name__ == "__main__":
    # A deliberately mis-normalized model proposal: data ratios don't sum to 1,
    # one hole_ratio is out of [0,1], to exercise the projection step.
    bad_proposal: EnvConfig = {
        "3x3":  SizeConfig(data_ratio=0.10, hole_ratio=0.20, wait_ratio=0.30),
        "4x4":  SizeConfig(data_ratio=0.20, hole_ratio=0.25, wait_ratio=0.30),
        "5x5":  SizeConfig(data_ratio=0.30, hole_ratio=0.30, wait_ratio=0.35),
        "6x6":  SizeConfig(data_ratio=0.30, hole_ratio=0.30, wait_ratio=0.35),
        "7x7":  SizeConfig(data_ratio=0.30, hole_ratio=0.35, wait_ratio=0.40),
        "8x8":  SizeConfig(data_ratio=0.35, hole_ratio=0.35, wait_ratio=0.40),
        "9x9":  SizeConfig(data_ratio=0.35, hole_ratio=0.40, wait_ratio=0.40),
        "10x10": SizeConfig(data_ratio=0.02, hole_ratio=1.40, wait_ratio=0.45),  # over 1.0
    }

    print("Before projection, data ratios sum to:",
          sum(c.data_ratio for c in bad_proposal.values()))

    fixed = project_config(bad_proposal)

    print("After projection, data ratios sum to:",
          round(sum(c.data_ratio for c in fixed.values()), 6))
    for size in MAP_SIZES:
        c = fixed[size]
        print(f"  {size}: data_ratio={c.data_ratio:.4f} "
              f"hole_ratio={c.hole_ratio:.4f} wait_ratio={c.wait_ratio:.4f}")
