# Slow_Update.md — reference reconstruction (SkillOpt §3.6, Appendix C.2)

Role: the epoch-wise slow update — SkillOpt's momentum term. Runs once per
epoch boundary, not once per step.

## Input
- The same set of training items (default 20, §4), re-sampled and re-run
  under **both** the previous epoch's skill and the current epoch's skill.
- The four-way bucketing of outcomes: improvements, regressions, persistent
  failures, stable successes.

## Task
Write longitudinal guidance that addresses **the training model directly**
(i.e. reads like an instruction inside the skill file itself, not a note to
a future optimizer — that's Meta_Skill.md's job). Focus on editing
directions that were *stable* across the two epochs, not on the current
step's noise.

## Output
A single markdown block, written to replace the contents between:

    <!-- SLOW_UPDATE_START -->
    ...guidance here...
    <!-- SLOW_UPDATE_END -->

This is the only part of the skill file that ordinary step-level edits
(Analyst_Error/Success + Merge_Final + Ranking) are forbidden from touching
— see the `protected_ids` check in `skill_patch.py`. The candidate skill
produced by a slow update still has to clear the same validation gate as
any other step (§3.5).
