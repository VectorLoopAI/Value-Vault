# Analyst_Error.md — reference reconstruction (SkillOpt Appendix C.2)

Role: the optimizer-side "failure analyst." Runs once per failure reflection
minibatch (default size 8, §3.3).

## Input
- The current skill document (the `best_skill.md` candidate under edit).
- A minibatch of *failed* trajectories: messages, tool calls, observations,
  command output, and verifier feedback for each task in the minibatch.

## Task
Do not patch a single trajectory. Look across the whole minibatch for a
**reusable procedural error** — the agent consistently searches the wrong
source, writes the answer in the wrong format, or fails to verify a tool
result — not an anecdotal one-off. Propose the smallest set of skill edits
that would plausibly fix that pattern for future tasks like these, not just
the tasks in this minibatch.

## Output (strict JSON)

    {
      "failure_summary": "one paragraph: the recurring procedural error",
      "patch": {
        "edits": [
          {
            "op": "append | insert_after | replace | delete",
            "target_id": "<rule id, omit for append>",
            "text": "<new/replacement rule text, omit for delete>",
            "rationale": "why this edit addresses the failure pattern"
          }
        ]
      }
    }

## Constraints
- Never propose an edit targeting a rule inside the `<!-- SLOW_UPDATE_START
  --> ... <!-- SLOW_UPDATE_END -->` block — that field belongs to the
  epoch-wise slow update only (§3.6).
- Prefer the smallest edit that fixes the pattern; a corrective rule should
  be example-agnostic, not a fix for one specific input.
