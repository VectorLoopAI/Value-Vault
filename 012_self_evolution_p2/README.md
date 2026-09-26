# 013 — Self-Evolution Part 2: see Part 1's Value Vault

This episode (Part 2 of the "writer vs. reader" self-evolution two-parter)
shares its Value Vault with **Part 1** — the harness-updating /
harness-benefit metric definitions, the locked experimental controls, and
every data table discussed across both videos live in one place, not
duplicated per part:

    ../../012_self_evolution_p1/value_vault/

**Part 1 video:** https://www.youtube.com/watch?v=Eq36hOq9mAY
**Part 2 video:** https://www.youtube.com/watch?v=0y1x2y3yLB0

Source paper: *"Harness Updating Is Not Harness Benefit: Disentangling
Evolution Capabilities in Self-Evolving LLM Agents"* — Minhua Lin,
Juncheng Wu, Zijun Wang, Zhan Shi, Yisi Sang, Bing He, Zewen Liu, Tianxin
Wei, Zongyu Wu, Zhiwei Zhang, Dakuo Wang, Xiang Zhang, Benoit Dumoulin,
Cihang Xie, Yuyin Zhou, Suhang Wang, Hanqing Lu (The Pennsylvania State
University / UC Santa Cruz / Amazon / Emory University / UIUC /
Northeastern University, 2026).

If you're looking for this episode's own numbers — the non-monotonic
harness-benefit curve (peak 19.3 pp at Qwen3-235B on SWE-bench), the
SLR 0.961 / HFR 0.350 activation-vs-adherence split, the phase-level drift
(-0.39 weak vs. -0.09 strong), and the SkillsBench exception (Haiku 4.5's
15.1 pp, Qwen3-32B tying Opus 4.6 at 5.8 pp) — those are argued in the
video itself and reproduced in `code/demo.py` in Part 1's folder (linked
above), which recomputes every headline claim from both parts against the
paper's own tables.
