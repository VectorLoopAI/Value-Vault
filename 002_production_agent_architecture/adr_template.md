# Six-Line Architecture Decision Record (ADR) — Agent Runtime

Fill in every row before you write the first line of orchestrator code (§ methodology Step 5:
"build the dashboard before the agent — the trace is the contract"). Each row names the pattern
you chose, the predicate that fired to choose it, and the failure signature you'd expect if you
picked wrong — that last column is what turns this ADR into a diagnostic later.

| # | Dimension | Pattern chosen | Predicate that fired | Expected failure signature if wrong |
|---|-----------|---------------|-----------------------|--------------------------------------|
| 1 | **Runtime class** | Conversational / Autonomous / Long-Horizon | one sentence: how long does one unit of work last, and does the world change mid-window? | wrong latency/consistency trade-off; e.g. treating a long-horizon process as conversational loses state across pauses |
| 2 | **Spine (State)** | P3 Event-Driven Sequencing / P5 Shared State Machine | P5 iff **all three** hold: (a) pauses > 1hr or external waits, (b) state at a pause is not reconstructible from the original input, (c) the world can change during the pause. Otherwise P3 (or reconstruct-on-demand if only (b) fails). | picking P3 when P5 was needed → **replay divergence** (same event, different downstream result on a newer model) |
| 3 | **Coordination** | P1 Hierarchical Delegation / P2 Scatter-Gather + Saga | P1 if single owner + independent sub-tasks + deterministic merge feasible. P2 if peers touch external systems with side-effects, partial failure must still produce a useful result, or a bad partial write costs more than a compensation log. | P1 without P2 on a side-effecting peer → uncompensated partial writes; P2 without P1 → no clear owner for merge conflicts |
| 4 | **Control** | P4 Supervisor + Gate (always, if any side-effect) / + P6 Human-in-the-Loop | P4 always if any external side-effect. Add P6 if a wrong action is legally/financially consequential, or "auditors will ask who decided this." | missing P4 → ungated writes reach production (e.g. the 90%-discount failure); missing P6 → no escalation path for consequential decisions |
| 5 | **Sequence** | build order for v1 | "dashboard before the agent": (1) state schema + observability, (2) gate + audit log, (3) orchestrator + one sub-agent, (4) remaining sub-agents, (5) P6 planes in order (kill switch, escalation, approval, throttling) | deferring (1)/(2) past v1 → no way to diagnose the failure that inevitably ships first |
| 6 | **Date / model version** | e.g. `2026-07-23 / claude-sonnet-4.6` | only this row depends on the model — the other five are model-agnostic | undated ADRs can't be used as the pinned reference for the quarterly drift diagnostic |

---

## Worked example (from the video's reference case)

| # | Dimension | Chosen | Predicate | Failure signature if wrong |
|---|-----------|--------|-----------|------------------------------|
| 1 | Runtime class | Long-Horizon | 90-day window, multiple agents, world changes mid-flight (product EOL at day −47) | treating it as Autonomous loses cross-pause state |
| 2 | Spine | P5 | all three fire: pauses run days; mid-window signals aren't reconstructible from the original input; the world moves under you | P3 here exposes the spine to replay drift on genuinely irrecoverable state |
| 3 | Coordination | P1 + P2 | one owner (the renewal row) + three sub-agents fan out; the contract sub-agent writes to billing (external side-effect) | P1 alone leaves billing writes uncompensated on partial failure |
| 4 | Control | P4 + full P6 | side-effects everywhere; discount decisions are financially consequential | no P6 → no escalation path for a merger/EOL edge case |
| 5 | Sequence | console-first | operational/business/compliance dashboards precede the first agent | agent ships before anyone can tell if it's working |
| 6 | Date/model | `2026-07-23 / claude-sonnet-4.6` | — | — |
