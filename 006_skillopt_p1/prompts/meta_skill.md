# Meta_Skill.md — reference reconstruction (SkillOpt §3.6, Appendix C.2)

Role: write the optimizer-side meta skill — a document that never ships
with the target model. It exists purely to make future reflection/merge/
ranking calls smarter about *this specific training run*.

## Input
- The run's `edit_apply_report.json` history: which edits were proposed,
  accepted, or rejected, and the score each rejected edit cost.
- The rejected-edit buffer (`gate.py`'s `epoch_buffer`).

## Task
Write guidance that addresses **the FUTURE OPTIMIZER directly, not the
training model** — e.g. "edits proposing X-style formatting fixes have been
rejected 3 times this run; the actual failure is Y, propose edits against Y
instead." This is prepended to future Analyst_Error / Analyst_Success /
Merge_Final calls in the same run.

## Output
A markdown document, kept entirely separate from `best_skill.md`. Never
included in the deployed file, never sent to the target model — only ever
sent back into this optimizer's own future prompts (§3.6: "the deployed
skill remains compact and portable, while training benefits from a richer
record of the editing process").
