# manager_action_schema.md — the manager's action contract (reconstructed)

AdaCoM's manager emits a JSON list of "operations" at every decision point
(paper §3.1). The paper's own manager prompt lives in its Appendix H, which
is not reproduced verbatim in the source note behind this episode —
everything below is a faithful reconstruction of the *fields and rules*
the paper states explicitly, written as a usable system-prompt contract.
Treat the field semantics as `(paper)`; treat the exact prompt
wording/phrasing as `(illustrative)` — swap in your own house style
freely.

## Fields (paper, exact)

Every operation has exactly four fields:

1. **`ids`** — list[int]. The message ID(s) this operation targets. Must
   be **consecutive**.
2. **`role`** — one of `SYSTEM`, `USER`, `ASSISTANT`. The role assigned to
   the resulting message.
3. **`justification`** — a short rationale for the edit. Elicits the
   manager's reasoning and is **stripped before the agent ever sees** the
   resulting context — it exists purely to make the manager think, not to
   inform the agent.
4. **`new_content`** — string. Empty deletes the targeted messages
   entirely. Non-empty rewrites or merges them into one new message with
   the given role and content.

Messages untouched by any operation are copied through unchanged. An empty
operation list leaves the context exactly as it was.

## Suggested system prompt (illustrative wording, paper-accurate semantics)

> You are managing the context of a frozen downstream agent. You will be
> shown the current message list, each message with a unique integer id.
> Emit a JSON list of operations. Each operation has exactly four fields:
> `ids` (a list of consecutive message ids you are editing), `role`
> (`SYSTEM`, `USER`, or `ASSISTANT`), `justification` (a short private
> rationale — the agent will never see this field), and `new_content`
> (leave empty to delete the targeted messages, or provide replacement
> text to rewrite/merge them into one message). Any message not covered by
> an operation is passed through unchanged. If the current context does
> not need editing, emit an empty list. Optimize for what the downstream
> agent needs to succeed at its task — not for a shorter context per se.

## One fixed exception (MCP-Bench-Wiki only, paper)

Whenever a `get_article` tool result is appended to the context, run an
`extract` operation before the next agent step, regardless of what the
manager's learned policy would otherwise choose — trained into both the
SFT and RL data specifically to prevent unbounded growth from full
Wikipedia articles.
