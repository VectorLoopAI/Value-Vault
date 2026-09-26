# 011 — Agent Scaling Laws Part 2: see Part 1's Value Vault

This episode (Part 2 of the Agent Scaling Laws two-parter) shares its Value
Vault with **Part 1** — the EFC scoring system discussed across both videos
(the four-gate event score, the raw-cost and task-demand formulas, the
no-oracle Estimated-EFC / NRS-EFC estimators this episode introduces, the
harness-efficiency decomposition, and the EFC-ADAPTER ledger/ROI control
layer) lives in one place, not duplicated per part:

    ../../010_agent_scaling_laws_p1/value_vault/

**Part 1 video:** https://www.youtube.com/watch?v=yugJQaT57Uc
**Part 2 video:** https://www.youtube.com/watch?v=OAvCZqOs6Oo

Source paper: *"Scaling Laws for Agent Harnesses via Effective Feedback
Compute"* — Xuanliang Zhang, Dingzirui Wang, Keyan Xu, Qingfu Zhu, Wanxiang
Che (Harbin Institute of Technology, 2026).

If you're looking for the results this episode covers specifically — the
negative-R² result for every raw-compute baseline on pooled real traces,
NRS-EFC/D_task reaching R² = 0.93, the pre-registered prospective holdout,
the SWE-bench H0/H3-beats-H5/H6 reversal, and EFC-ADAPTER's 61.2% → 68.2%
pass-rate lift at roughly 60% lower raw cost — those are argued in the
video itself. The reproducible artifact behind *both* episodes, including
`estimated_efc.py`, `nrs_efc.py`, `efficiency.py`, and `efc_adapter.py` (the
modules Part 2 specifically introduces), is in Part 1's folder linked above.
