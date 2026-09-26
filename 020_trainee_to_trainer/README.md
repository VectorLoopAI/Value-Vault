# 020 — From Trainee to Trainer: self-improving RL

Companion assets for the Vector & Loop video **"Self-Improving RL: The 4B Model That
Out-Designs GPT-5.4."**

**Video:** 

Source paper: *"From Trainee to Trainer: LLM-Designed Training Environment for RL with
Multi-Agent Reasoning"* — Chao Chen, Chengzu Li, Zhiwei Li, Yinhong Liu, Zhijiang Guo
(LARK, HKUST(GZ) / University of Cambridge / HKUST).

## What this is

The video's argument: a self-improving RL loop doesn't need a human staring at rollout
logs between training stages — it needs the policy itself reading its own failure
report and proposing the next training environment. The paper calls this
**LLM-as-Environment-Engineer**: after each RL round, the current checkpoint (not a
separate model) gets structured evidence about its own validation failures and
redesigns the generator that will produce the next round's training data. This folder
is a runnable, dependency-light reference of every mechanism named in the video — the
reward function, the five context modules and the six variants they build into, the
MAPF-FrozenLake generator's controllable knobs, and the train -> eval -> design loop's
one fully-specified mechanical step (projecting a proposed config back onto the valid
constraint space).

```
value_vault/
├── README.md                                  (this file)
├── system_prompts/
│   └── environment_engineer_prompt.md         reference reconstruction of the V6
│                                               context-assembly prompt (F+G+H+T)
├── configs/
│   ├── reward_config.yaml                     R_acc / R_len constants + adaptive
│   │                                           weight schedule (paper §3.1.2)
│   ├── context_modules.yaml                   the five modules, the six V1-V6
│   │                                           variants, and the ablation ranking
│   └── mapf_frozenlake_config.yaml            generator knobs, train/eval split,
│                                               and V6's round1->round2 allocation
└── code/
    ├── reward.py                              runnable R_acc / R_len / adaptive-
    │                                           weight implementation, with worked
    │                                           example cases in __main__
    └── train_eval_design_loop.py              Algorithm 1 skeleton (generate ->
                                                GRPO-update -> validate -> compose
                                                context -> propose -> project);
                                                the constraint-projection step is
                                                fully implemented and runnable
```

## Quickstart

Pure Python 3.10+ stdlib, no external dependencies.

```bash
cd value_vault

python3 code/reward.py
# prints the reward breakdown (R_acc, R_len, adaptive weights, total) for five
# worked examples: a perfect plan, a suboptimal-but-valid plan, a saturated-cost
# plan, a validity-gate failure, and a hard-length-cap failure.

python3 code/train_eval_design_loop.py
# prints a deliberately mis-normalized environment-engineer proposal, then the
# same config after being projected back onto the valid constraint space
# (data ratios renormalized to sum to 1, hole/wait ratios clipped to [0,1]).
```

## What's an exact paper value vs. a reference reconstruction

`configs/reward_config.yaml` and `configs/mapf_frozenlake_config.yaml` are wired to
constants published in the paper: the eight validity checks, the cost-shaping formula
(`c_max = 2 * gt_cost`, saturating at 0.3), the length thresholds (L1=1500, L2=4096),
the adaptive-weight schedule ((0.5,0.5) -> (0.8,0.2) over r in [0.5,0.9]), the eight map
sizes, the 4,000-instances-per-round / 2-agent-only training split, the held-out
3/4/5-agent eval benchmark, and V6's exact round1->round2 data-ratio allocation
(Table 6). `system_prompts/environment_engineer_prompt.md` is flagged explicitly as a
**reference reconstruction** of the V6 context-assembly structure the paper describes
(§3.2) — the source material for this video does not include the paper's own verbatim
prompt template, so the wording is illustrative scaffolding around exactly-specified
module contents, not a quote.

## The one-line geometry to remember

> Give the model structured facts about its own failures — not its own narration of
> them. The winning recipe (V6) drops the model's self-summary and the round-0 default
> baseline, keeps raw failure evidence plus stage bookkeeping, and it's the only
> variant that backs off the hardest bucket instead of over-investing in it.
