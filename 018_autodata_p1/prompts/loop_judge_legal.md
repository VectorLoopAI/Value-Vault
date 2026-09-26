# Loop Judge (legal reasoning) — reference reconstruction (Autodata §3.2)

Role: the legal pipeline's acceptance decision-maker. Deliberately has **no
hard-coded numeric thresholds** — porting the CS domain's fixed thresholds
here would accept most of the broken static-generation pool, because legal
reasoning's failure mode is the opposite of CS's (too hard, not too easy).

## Input
- The client scenario + reference answer + rubric from question_writer_legal.md.
- The weak solver's rollout(s) and the strong solver's rollout(s) on this
  scenario.

## Task
Do not ask "is this hard enough" or compare against a fixed score. Ask
directly: **is this example GRPO-suitable?** — i.e., does it produce a
usable, non-degenerate training signal for RL. Consider:

1. **Weak-rollout spread** — are the weak solver's scores across its
   rollouts spread over a usable range, or clustered at (near-)zero? A
   prompt where 4-5 of 5 weak rollouts score exactly zero gives GRPO nothing
   to differentiate, even if the "average" looks non-trivial.
2. **Strong-solver reliability** — does the strong solver succeed clearly
   and consistently enough to serve as a correctness anchor?
3. **Genuine reasoning gap** — is there a real capability difference being
   exercised, or is the weak solver just failing on formatting/parsing
   issues unrelated to the legal reasoning itself?

## Output (strict JSON)

    {
      "grpo_suitability": "high" | "medium" | "low",
      "accept": true | false,
      "reasoning": "<why, referencing weak-rollout spread and strong-solver reliability>",
      "revision_guidance": "<only if accept=false — what to change next round>"
    }

## Notes
`accept` is true only for "high" (occasionally "medium" with strong
revision_guidance already incorporated) verdicts. This is a **qualitative**
gate — `acceptance_gate.py`'s `legal_acceptance()` intentionally does not
reimplement this as a numeric formula; it passes the judge's own `accept`
field through, because reducing "GRPO-suitable" to a fixed threshold is
exactly the mistake this domain's design avoids.
