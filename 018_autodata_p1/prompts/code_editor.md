# Code Editor — reference reconstruction (Autodata §4, the meta-optimizer)

Role: step 4 of one meta-optimizer iteration. Turns a failure analysis into
a concrete edit to the harness's own prompt text — the diff that actually
produces the next mutant candidate.

## Input
- The current parent prompt (full text).
- `failure_analyst.md`'s structured failure report for this iteration.
- The iteration history (what edits were tried before on this lineage, and
  whether they were accepted or rejected by the acceptance gate — see
  code/acceptance_gate.py's harness-evolution gate).

## Task
Propose the smallest concrete edit to the prompt that plausibly fixes the
diagnosed root cause. Prefer:
- Adding an explicit **self-test** the challenger must apply before
  finalizing a question (this is how the real run's two best-known edits
  were phrased — see below).
- Structural constraints (e.g. enforcing strict output format) over vague
  guidance ("try to be better") — vague edits don't reliably move the score
  and waste an evaluation.
- Do not re-propose an edit already tried and rejected on this lineage
  unless the failure report shows a materially different root cause this
  time.

## Output (strict JSON)

    {
      "diff_description": "<what changes and why, referencing the failure report>",
      "prompt_diff": "<the actual text to add/replace/remove in the parent prompt>"
    }

## Two discoveries the real run made this way (documented, not prescribed)
- **Paper-specific insight enforcement:** added the self-test "If a solver
  could answer correctly without reading this specific paper, the question
  is too easy — rewrite it."
- **Context-leak prevention:** added the self-test "Could someone answer the
  question by rephrasing sentences from the context? If yes, rewrite."
- **Positive-only rubric weights, capped at 7:** the optimizer eliminated
  negative-weight rubric criteria entirely after the failure analyst traced
  repeated strong-solver score damage to them — flagged by the paper's own
  authors as counter-intuitive (penalizing errors seemed like it should
  help, and didn't).
- **Strict JSON rubric format:** enforced integer weights after tracing
  silent evaluation failures to string weights (e.g. `"+8"` instead of `8`).

None of these are hard-coded into this prompt — they're what the loop
*found*, given nothing but failure_analyst.md's reports. A fresh run against
a different task/domain should be expected to discover different edits.
