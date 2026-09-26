# 008/009 — AdaCoM: a trained context manager for a frozen agent

Companion assets for the Vector & Loop two-part episode **"Context
Engineering for a Frozen Agent (Part 1)"** / **"Context Engineering: Does
One Manager Fit All? (Part 2)."** This one folder is shared by both parts —
see `videos/009_adacom_p2/value_vault/README.md` for the pointer used
there.

**Part 1 video:** https://www.youtube.com/watch?v=u03YVesuo6Q
**Part 2 video:** https://www.youtube.com/watch?v=udEQo_6nInU

Source paper: *"Learning Agent-Compatible Context Management For
Long-Horizon Tasks"* — Lu Yi, Runlin Lei, Liuyi Yao, Yuexiang Xie, Yuyang
Li, Wenhao Zhang, Zhewei Wei, Yaliang Li, Jian-Yun Nie (Renmin University of
China; Tongyi Lab, Alibaba Group; Beijing University of Posts and
Telecommunications; Université de Montréal, 2026).

## What this is

The episode's argument: context management doesn't have to live inside the
agent you're trying to help. AdaCoM trains a *separate*, small (4B) model
that sits in front of a completely frozen agent and edits the message list
before every step — delete, merge, rewrite, or leave alone — via a flexible
four-field JSON operation, RL-trained with a sparse trajectory-level outcome
reward plus three cheap rule-based process rewards. The agent's own weights
never move; the gradient only ever touches the manager's own tokens. This
folder is a runnable, dependency-free reference implementation of that
mechanism — not the paper's production code, but a faithful reproduction
of every schema/reward/estimator named in the video, wired to the paper's
own published hyperparameters where they're published.

```
value_vault/
├── README.md                          (this file)
├── configs/
│   └── adacom_config.yaml             every default hyperparameter, paper values flagged
├── prompts/
│   └── manager_action_schema.md       the four-field edit schema as a usable system-prompt contract
└── code/
    ├── context_ops.py                 Message/Operation + apply_operations (the manager's action space)
    ├── process_rewards.py             the three rule-based process rewards + BrowseComp-Plus gold-doc bonus
    ├── advantage.py                   the two-level (task + step) advantage estimator
    └── demo.py                        end-to-end toy loop tying all three together
```

## Quickstart

Zero external dependencies — Python 3.10+ stdlib only.

```bash
cd value_vault/code
python3 demo.py
```

`demo.py` applies a manager action to a small 5-message context (one merge,
one delete), scores a manager step against the three rule-based rewards,
then runs the two-level advantage estimator over a toy 2-rollout group where
both rollouts share the same outcome reward — the exact case the paper
calls out, where the task-level advantage term vanishes and the step-level
(process-reward) term becomes the only learning signal in that group.

## What's an exact paper value vs. an illustrative default

`configs/adacom_config.yaml` marks every constant `(paper)` or
`(illustrative)`. The manager backbone, context windows, GRPO/SFT
hyperparameters, and reward *rules* are wired in exactly as published:
Qwen3-4B-Instruct backbone, 32,768-token manager input / 4,096-token
output, GRPO group size 8 via Trinity-RFT, rollout batch 32, training batch
768, learning rate 5e-6, KL coefficient 0.006, PPO clip 0.2, temperature
1.0, 35-iteration rollout cap, process-reward weight alpha = 0.1. The paper
names and motivates the three process-reward rules (token-limit,
redundant-action, format) but does not publish their exact numeric
magnitude — those are flagged `(illustrative)` in the config and in
`process_rewards.py`; calibrate them against your own judge/environment.
Likewise, the paper's own manager prompt lives in its Appendix H, which the
backlog source note for this episode doesn't reproduce verbatim —
`prompts/manager_action_schema.md` is a faithful reconstruction of the
*fields and rules*, not a transcription of the paper's exact wording.

## The one-line geometry to remember

> The agent never gets a gradient. Everything you saw in this episode came
> from training a separate model whose only output is a JSON list of edits
> to the agent's own context — and Part 2 shows that trained edit-style is
> portable to agents the manager never trained against.
