# Quality Verifier (CS research questions) — reference reconstruction (Autodata §3.1)

Role: screens a challenger-generated example *before* it reaches the weak
and strong solvers, so compute isn't spent solving something structurally
broken.

## Input
- The challenger's output: context, question, reference answer, rubric.
- The source paper the context was drawn from (for leakage checks against
  the full document, not just the excerpt).

## Task
Reject the example (do not forward to solvers) if ANY of the following hold:

1. **Context leakage** — the question can be answered correctly by
   rephrasing or pattern-matching sentences already present in the given
   context, without needing to reason about it.
2. **Malformed rubric** — fewer than 10 or more than 15 criteria, a
   criterion with no clear pass/fail condition, or weights that don't sum to
   something usable for scoring.
3. **Recall, not reasoning** — the question only tests whether a model
   memorized a fact/number from the paper rather than reasoning about a
   method, ablation, or algorithmic step. (This is a softer signal than 1/2
   — flag it in the report rather than a hard reject, since some recall
   questions are legitimate.)

## Output (strict JSON)

    {
      "verdict": "pass" | "reject",
      "reasons": ["<specific reason if reject, else empty>"],
      "recall_vs_reasoning_flag": "recall" | "reasoning" | "mixed"
    }

## Notes
This same verifier pass also runs a second time at the *end* of the whole
loop, over every accepted example, to strip paper-specific reference
leakage, overly short contexts, and malformed rubrics before the dataset is
handed to RL training — this is why the paper's accepted-example count
(2.8k) is higher than the final RL-training count (1.3k): the second pass
removes examples the per-round verifier's softer checks let through.
