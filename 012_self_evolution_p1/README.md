# 012/013 — Disentangling self-evolution: the writer vs the reader

Companion assets for the Vector & Loop two-part episode **"Self-Evolving
AI Agents: A 9B Model Out-Writes Opus (Part 1)"** / **"Self-Evolving AI
Agents: Opus Benefits Least (Part 2)."** This one folder is shared by both
parts — see `videos/013_self_evolution_p2/value_vault/README.md` for the
pointer used there.

**Part 1 video:** https://www.youtube.com/watch?v=Eq36hOq9mAY
**Part 2 video:** https://www.youtube.com/watch?v=0y1x2y3yLB0

Source paper: *"Harness Updating Is Not Harness Benefit: Disentangling
Evolution Capabilities in Self-Evolving LLM Agents"* — Minhua Lin,
Juncheng Wu, Zijun Wang, Zhan Shi, Yisi Sang, Bing He, Zewen Liu, Tianxin
Wei, Zongyu Wu, Zhiwei Zhang, Dakuo Wang, Xiang Zhang, Benoit Dumoulin,
Cihang Xie, Yuyin Zhou, Suhang Wang, Hanqing Lu (The Pennsylvania State
University / UC Santa Cruz / Amazon / Emory University / UIUC /
Northeastern University, 2026).

## What this is

The episode's argument: "self-evolution improved our agent by X%" is
quietly averaging over two separable capabilities — **harness-updating**
(an evolver model writes edits to prompts/skills/memory) and
**harness-benefit** (a solver model reads and follows them) — and they
scale in opposite directions. This folder is a runnable, dependency-free
reference implementation of the paper's own decomposition methodology
(§3.3), pre-loaded with every number named in the two videos, so you can
recompute the headline claims yourself rather than take the video's word
for them.

```
value_vault/
├── README.md                              (this file)
├── configs/
│   ├── evolution_protocol.yaml            the agent/evolver formalism + every locked control (§4.1)
│   └── benchmarks.yaml                    SWE-bench Verified / MCP-Atlas / SkillsBench specs
└── code/
    ├── metrics.py                         Delta_update / Delta_benefit / base-capability formulas (§3.3)
    ├── data_tables.py                     every published number from both episodes, source-tagged
    └── demo.py                            recomputes every headline claim from the two videos
```

## Quickstart

Zero external dependencies — Python 3.10+ stdlib only.

```bash
cd value_vault/code
python3 demo.py
```

`demo.py` walks through, in order: (1) the evolver-side flatness claim —
the known best/worst evolver cells per benchmark, all consistent with the
paper's own "at most 3.1 pp spread" headline; (2) the agent-side
harness-benefit table, recomputing the non-monotonic peak on SWE-bench and
MCP-Atlas, and printing the SkillsBench exception explicitly rather than
smoothing it away; (3) the activation-vs-adherence separation — Qwen3-235B
vs. Opus 4.6, same skill-load rate (SLR), less than half the
harness-following rate (HFR); (4) the phase-level adherence drift for a
weak/mid/strong model; (5) the extreme-pairing stress test.

## What's an exact paper value vs. a partial reconstruction

`code/data_tables.py` tags every number `(paper, verified)` — meaning it's
copied from a table or verified-reconstruction in the backlog source note
— or `(paper, partial)` for the per-evolver Delta_update breakdown, where
only the specific models named on-camera in each video are recorded (the
paper states the full 7-evolver spread never exceeds 3.1 pp, but this note
only captured the best/worst-named cells per benchmark, not the complete
7x3 grid). Nothing in this folder is invented or interpolated — cells not
sourced from the script or backlog note are simply absent, not guessed.

## The one-line geometry to remember

> One end-to-end "self-evolution" score is doing two jobs. Writing a good
> harness update is a competence threshold — a 9B model clears it about as
> well as Claude Opus 4.6. Benefiting from one is a skill with its own
> failure modes — activation (does the agent load it) and adherence (does
> it keep following it) — and those are the two things actually worth
> instrumenting in your own agent stack.
