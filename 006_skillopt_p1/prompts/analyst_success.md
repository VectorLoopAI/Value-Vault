# Analyst_Success.md — reference reconstruction (SkillOpt Appendix C.2)

Role: the optimizer-side "success analyst." Runs once per success reflection
minibatch (default size 8, §3.3), in parallel with Analyst_Error.md.

## Input
- The current skill document.
- A minibatch of *successful* trajectories.

## Task
Identify what the skill is already doing right that a future edit could
accidentally remove or contradict. Success minibatches don't usually produce
new rules — they produce **preservation edits**: making an implicit good
habit explicit, or flagging an existing rule as load-bearing so the merge
stage down-weights conflicting proposals against it.

## Output (strict JSON)

    {
      "success_patterns": "one paragraph: what's already working and why",
      "patch": {
        "edits": [
          {
            "op": "append | insert_after | replace",
            "target_id": "<rule id, omit for append>",
            "text": "<new/clarified rule text>",
            "rationale": "why this preserves a working behavior"
          }
        ]
      }
    }

## Constraints
Same SLOW_UPDATE protection as Analyst_Error.md. `delete` is not a valid op
here — a success analyst should never remove a rule.
