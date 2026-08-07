# Ranking.md — reference reconstruction (SkillOpt §3.4, Appendix C.2)

Role: order the merged edit pool so the optimizer knows which top-`L_t`
edits to actually apply this step.

## Input
- The merged edit pool from Merge_Final.md (each edit carries `support_count`).
- The current textual learning rate `L_t` for this step (`L_t` itself comes
  from the schedule in `learning_rate_schedule.py` — this prompt only ranks
  and returns indices, it does not decide the budget).

## Ranking criteria
The paper names four criteria but does not publish numeric weights between
them; `configs/skillopt_config.yaml`'s `ranking_criteria` block is an
**illustrative default**, not a reproduced constant:
1. **Systematic impact** — how many trajectories/analyst calls support it
   (`support_count`, a direct signal).
2. **Complementarity** — does it interact well with already-accepted rules,
   or does it overlap/contradict them.
3. **Generality** — does it fix a class of failures or one specific input.
4. **Actionability** — is it a concrete, checkable instruction, or vague
   advice the target model can't operationalize.

## Output (strict JSON)

    {
      "ranked_indices": [0, 2, 1],
      "top_lt_indices": [0, 2]
    }

`ranked_indices` indexes into the input edit pool, best first.
`top_lt_indices` is `ranked_indices[:L_t]` — the actual edits that get
applied this step (see `skill_patch.py` + `learning_rate_schedule.py`'s
`clip_to_budget()`).
