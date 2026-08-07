# Merge_Final.md — reference reconstruction (SkillOpt Appendix C.2)

Role: hierarchical merge of the analyst pool (§3.3). Runs after all
Analyst_Error / Analyst_Success calls for the current rollout batch (or
accumulated batches, if gradient-accumulation-style reflection is in use).

## Pipeline
1. **Merge_Failure.md** — consolidate all failure-analyst edits among
   themselves: drop duplicates, drop edits that contradict each other
   (keep the one with the higher combined support), drop anything too
   example-specific to generalize.
2. **Merge_Success.md** — the same consolidation pass over success-analyst
   edits only.
3. **Merge_Final.md** (this stage) — combine the two consolidated pools,
   **with priority given to failure-driven corrections** whenever a
   success-preservation edit and a failure-correction edit conflict.

## Output (strict JSON)

    {
      "edits": [
        {
          "op": "append | insert_after | replace | delete",
          "target_id": "<rule id, omit for append>",
          "text": "<rule text, omit for delete>",
          "support_count": 0,
          "source": "failure | success"
        }
      ]
    }

`support_count` is what `Ranking.md`'s "systematic impact" criterion reads
directly off — an edit sixteen analyst workers proposed independently ranks
above one only a single worker suggested.
