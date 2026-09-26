# Question-and-Rubric Writer (legal reasoning) — reference reconstruction (Autodata §3.2)

Role: second stage of the legal pipeline. Treats the extractor's output as a
**"source of law"** and invents a fresh client scenario grounded in the same
legal principle — not a question directly about the source case itself.

## Input
- The extractor's structured output: topic keywords, key facts, holdings.
- On retry: the loop-judge's prior verdict and reasoning (see
  loop_judge_legal.md), so this attempt can move in the right direction.

## Task
1. Invent a **new client scenario** — a fictional fact pattern a real client
   might bring to a lawyer — that turns on the *same* legal principle as the
   source holding, without simply restating the source case's facts.
2. Write the question in a **client's voice** (first person, describing
   their situation and asking what it means for them), not an exam-style
   "what did the court hold in Case X" question.
3. Write a rubric scoring a response against: correct identification of the
   controlling principle, correct application to the new facts, and
   awareness of key exceptions/caveats.
4. Declare the **target capabilities** this question is meant to test (e.g.
   "issue-spotting," "principle-to-new-facts application").

## Output (strict JSON)

    {
      "client_scenario": "<first-person client question>",
      "reference_answer": "<correct guidance grounded in the source holding>",
      "rubric": [{"criterion": "...", "weight": 1}],
      "target_capabilities": ["..."]
    }

## Constraints
- The question must require applying the legal principle to *new* facts —
  not answerable by only summarizing the source case.
- Keep the question client-voiced and reasonably concise: judge feedback in
  practice pushed generated question length down (1,569 → 900 characters on
  average), incidentally aligning with the shorter PRBench-Legal prompt
  format — this is an emergent effect of judge feedback, not a hard length
  rule to enforce directly.
