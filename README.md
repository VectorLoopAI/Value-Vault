# Value Vault

Runnable companion code for every [Vector & Loop](https://www.youtube.com/@VectorAndLoop) video. Each folder ships the diagrams, configs, prompts, and reference implementations promised at the end of the video -- no dependencies beyond Python 3.10+ stdlib unless noted.

## Series A -- The Agent Harness

| # | Video | Folder | One-liner |
|---|-------|--------|-----------|
| 001 | **The Blind Spot in Every Multi-Agent Coder** | [`001_code_as_agent_harness/`](001_code_as_agent_harness/) | Three-layer harness diagram, permission-tier checklist, Plan-Execute-Verify template |
| 002 | **The Seam Nobody Names** | [`002_production_agent_architecture/`](002_production_agent_architecture/) | Six runtime patterns (P1-P6), spine-decision predicate, drift-diagnostic procedure, ADR template |
| 003 | **It Deleted Its Own File** | [`003_self_harness/`](003_self_harness/) | Weakness-mining loop, acceptance rule, three case-study edits (MiniMax / Qwen / GLM-5) |
| 004 | **Fix the Interface, Not the Model** | [`004_adapting_the_interface/`](004_adapting_the_interface/) | LIFE-HARNESS four-layer pipeline, failure-mode taxonomy, contract/skill/action/trajectory layers |
| 005 | **The 20B Model That Beats GPT-5.4** | [`005_harness_1_search/`](005_harness_1_search/) | Working-memory state machine, reward function, policy/entailment prompts, SFT+RL configs |

## Quickstart

```bash
git clone https://github.com/VectorLoopAI/Value-Vault.git
cd Value-Vault

# pick any episode and run its demo
python3 001_code_as_agent_harness/pev_loop.py
python3 002_production_agent_architecture/spine_decision_predicate.py
python3 003_self_harness/weakness_mining.py
cd 004_adapting_the_interface && python3 -m life_harness.pipeline && cd ..
pip install pyyaml && python3 005_harness_1_search/code/demo.py
```

Each folder has its own README with full context: what the video promised, what the code does, how to adapt it to your own agent stack.

## Philosophy

Every video closes with a concrete takeaway you can run today. No slides, no "subscribe for the code" -- it's here, it's free, and it works out of the box. If a constant came from a paper, it's marked `(paper)`; if we filled in a gap, it's marked `(illustrative default)`.

## License

MIT
