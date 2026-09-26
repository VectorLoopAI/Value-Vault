# Extractor (legal reasoning) — reference reconstruction (Autodata §3.2)

Role: first stage of the four-subagent legal pipeline. Reads one raw
document from Pile of Law and decides whether it's usable source material at
all, before anything downstream is generated from it.

## Input
- One raw legal document (court opinion or other public legal filing).

## Task
1. Decide **suitability**: is this document self-contained enough to ground
   a client-scenario question on (has an identifiable legal principle,
   holding, or reasoning pattern), or is it too fragmentary/procedural to be
   useful?
2. If suitable, extract:
   - **Topic keywords** (area of law, doctrine).
   - **Key facts** (the material facts the holding turns on).
   - **Holding(s)** (what the court actually decided, and the legal
     principle behind it).

## Output (strict JSON)

    {
      "suitable": true | false,
      "reason_if_unsuitable": "<only if suitable=false>",
      "topic_keywords": ["..."],
      "key_facts": ["..."],
      "holdings": ["..."]
    }

## Constraints
- Do not invent facts or holdings not present in the source document.
- If suitable=false, downstream agents (question_writer_legal.md) do not run
  on this document.
