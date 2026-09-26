# 014/015 — PreAct: compile a run once, replay it, then check what you kept

Companion assets for the Vector & Loop two-part episode **"Computer Use
Agent: Compile Once, Never Think Again (Part 1)"** / **"Computer Use Agent:
The Check That Saves Its Memory (Part 2)."** This one folder is shared by
both parts — see `videos/015_preact_p2/value_vault/README.md` for the
pointer used there.

**Part 1 video:** https://www.youtube.com/watch?v=Drv9UDuMkW8
**Part 2 video:** https://www.youtube.com/watch?v=NpQuI26iSww

Source paper: *"PreAct: Computer-Using Agents That Get Faster On Repeated
Tasks"* — Bojie Li (Pine AI)

## What this is

The episode's argument in one line: a computer use agent that succeeds at a
task once can compile that run into a small, verified state-machine program
— replay it directly with zero per-step model calls, and it's faster; but
**replay succeeding is not the same as the task succeeding**, and the check
that catches the difference runs at a completely different moment than the
one everyone assumes. This folder is a runnable, dependency-free reference
implementation of both checks — Part 1's run-time verification and Part 2's
store-time gate — pre-loaded with every number named in the two videos, so
you can recompute the headline claims yourself rather than take the video's
word for them.

```
value_vault/
├── README.md                                    (this file)
├── configs/
│   ├── program_schema.yaml                      the P=(S,T,M,V) tuple, graph-vs-script, run-time verification (§3.2)
│   ├── verify_gate.yaml                         the store-time double gate, the audit, the fallback fix (§3.3, §4.3-4.6)
│   ├── benchmarks.yaml                          AndroidWorld / OSWorld / WebArena specs + protocol
│   └── contacts_add_contact.program.yaml        Listing 1 / Figure 4 -- the actual "Emilia Gonzalez program"
└── code/
    ├── state_machine.py                         Program/State/Transition + replay() -- "observe first, then act"
    ├── verify_gate.py                           the store-time AND-gate, mutative corpus, Table-4 cache-miss fix
    ├── data_tables.py                           every published number from both episodes, source-tagged
    └── demo.py                                  recomputes every headline claim from both videos
```

## Quickstart

Zero external dependencies — Python 3.10+ stdlib only.

```bash
cd value_vault/code
python3 demo.py
```

`demo.py` walks through, in order: (1) replaying the real 7-state Emilia
Gonzalez program (Listing 1) on a clean run and on a mid-execution mismatch,
showing the hand-off to the CUA fallback; (2) the exact same program under a
**lossy** run — full coverage, terminal reached, and yet the independent
evaluator says the goal wasn't met — and how the store-time gate rejects it
while run-time replay alone would not have noticed; (3) the Table 2
verify-gate ablation across all three platforms; (4) Table 3's five
reproducible coverage-100%/score-0 programs and the WebArena 48-of-48
collapse; (5) the Muscle-Mem head-to-head, before and after the one-line
cache-miss fallback fix; (6) the negative results (embedding retriever
beating the LLM selector) and the out-of-distribution generalization
headwind.

## What's an exact paper value vs. excluded on purpose

Every number in `code/data_tables.py` is tagged `(paper, verified)` or
`(paper, qualitative)` and traces to a specific figure, table, or stated
passage in `backlog/010_preact.md`. **Table 1 is deliberately never used
anywhere in this folder** — the backlog note flags it as badly
OCR-mangled/reconstructed from surrounding prose, so its fine-grained cells
are excluded on principle, not overlooked.

The **8.5–13× speedup figure is the WebArena wall-clock measurement
specifically** — see `SCOPED_SPEEDUP_NOTE` in `code/data_tables.py` and the
matching note in `configs/benchmarks.yaml`. Android and OSWorld replay speed
are reported only qualitatively in the paper ("near-free," "finishes in
seconds") — there is no separate multiplier for either platform anywhere in
this Value Vault, matching both scripts.

## The one-line geometry to remember

> Checking that an action fired is not the same as checking that the goal
> was met. PreAct runs that check twice, at two different moments — before
> every replayed action (Part 1, cheap, makes replay safe) and once more
> before a freshly compiled program is trusted into the corpus (Part 2,
> expensive, is what keeps the corpus from rotting). Store the program you
> run, and never keep one you haven't checked.
