# Harness Evolution Constraints (Codex-driven evolution loop)

As described in the paper's Step 3 and SEG 20–21 of the script. This is the constraint
checklist the harness-evolution prompt enforces on every proposed update to the four
layers. Treat it as a code-review checklist for any automated or human-written change to
your own harness, not just for the paper's specific method.

## Evolution loop (Algorithm 1, paraphrased faithfully)

```
repeat for N evolution rounds:
    1. Run the CURRENT frozen harness + frozen model on the training task set.
    2. Collect complete trajectories (observations, actions, feedback, outcomes).
    3. Annotate failures with the priority protocol
       (see failure_annotation_priority_protocol.md).
    4. Feed the coding agent:
         - the failed trajectories
         - the current contents of all four layers
         - the design criteria and constraints below
       and ask it to propose a MINIMAL, LOCALIZED update to exactly the layer(s)
       responsible for the dominant failure mode(s) observed this round.
    5. Apply the proposed update.
    6. Re-run the FULL training set (not just the previously-failing episodes) and
       check for regressions (see "Mandatory regression check" below).
    7. If the update causes a net regression, revert it and try a narrower fix.
    8. Freeze the harness once (a) coverage saturates or (b) the round budget is spent.
    9. Evaluate the frozen harness ONCE on the held-out test set. The test set is never
       touched, inspected, or referenced by name during evolution.
```

## Constraint checklist (enforce on every proposed update)

- [ ] **No test-label leakage.** The proposed update must not reference, encode, or have
      been informed by anything from the held-out evaluation set — only training
      trajectories and environment documentation.
- [ ] **No environment tampering.** Must not modify benchmark tasks, alter environment
      transition dynamics, or change evaluation criteria. The harness sits *outside* the
      environment; it never edits it.
- [ ] **Local and minimal.** Each update should touch the smallest surface that addresses
      the observed failure — a new `ΔC` line, one new guard in the action-realization
      layer, one new skill entry, one new regulation-tier message. Not a rewrite of a
      layer's entire logic.
- [ ] **Don't override ambiguous reasoning.** If the "correct" action is genuinely
      ambiguous given the task, the harness must not force a specific choice — it should
      only intervene where the environment's rules make an action *deterministically*
      wrong or right.
- [ ] **Mandatory regression check.** Before accepting the update, re-run the full
      training set and explicitly search for: actions the harness now blocks that were
      previously valid; guidance the harness now injects that is misleading for tasks
      unrelated to the failure being fixed; any drop in previously-passing episodes.
- [ ] **Auditability.** Every intervention must be traceable to a specific line/rule a
      human can read and point at — "this guard blocked this action because X" — never a
      diffuse, unexplainable change.

## Why this belongs in your own harness work

This discipline is what keeps an automatically-evolved harness safe to ship: it is edited
like production code (small diffs, regression tests, no peeking at the eval set) even
though the "editor" is a coding agent, not a human. Apply the same six checks to any
prompt-engineering or scaffold change your own team ships, harness-evolution loop or not.
