"""
demo.py — end-to-end toy walk-through tying every module in this folder
together: score a handful of feedback events, log them to the ledger,
compute harness efficiency + task-normalized feedback, apply the NRS-EFC
redundancy tax, and run EFC-ADAPTER's ranking/stop-rule over a batch of
candidate actions.

Zero external dependencies — Python 3.10+ stdlib only.
    cd value_vault/code
    python3 demo.py
"""

from __future__ import annotations

from efc_adapter import CandidateAction, EFCAdapter
from efc_score import FeedbackEvent, run_efc
from efficiency import HarnessDiagnosis
from nrs_efc import NRSGates, nrs_efc
from raw_cost import RunSpend
from task_demand import TaskDemandFactors


def main() -> None:
    print("=== 1. Score a toy trajectory's feedback events (the four gates) ===")
    events = [
        FeedbackEvent("checker_fired", informativeness=0.85, validity=1.0, relevance=0.8, memory_update=0.75),
        FeedbackEvent("unread_critique", informativeness=0.9, validity=0.6, relevance=0.7, memory_update=0.05),
        FeedbackEvent("repeated_stack_trace", informativeness=0.1, validity=0.9, relevance=0.05, memory_update=0.1),
    ]
    for e in events:
        print(f"  {e.event_id:24s} -> EFC_t = {e.score:.3f}")
    efc_total = run_efc(events)
    print(f"  run-level EFC(tau) = {efc_total:.3f}")

    print("\n=== 2. Normalize by raw cost and task demand ===")
    spend = RunSpend(n_tokens=42000, n_tool_calls=18, wall_time=210, n_ops=6)
    demand = TaskDemandFactors(
        min_steps=6, tool_ambiguity=1.4, state_pressure=1.2, obs_noise=0.3, verifier_visibility=0.4
    )
    diagnosis = HarnessDiagnosis("toy_run", efc=efc_total, raw_cost=spend.raw_cost, d_task=demand.d_task)
    print(f"  C_raw = {spend.raw_cost:.3f}   D_task = {demand.d_task:.3f}")
    print(f"  eta (harness efficiency)      = {diagnosis.eta:.3f}")
    print(f"  X = EFC/D_task (sufficiency)  = {diagnosis.task_normalized_feedback:.3f}")
    print(f"  diagnosis: {diagnosis.diagnose(eta_floor=0.05, x_floor=1.0)}")

    print("\n=== 3. NRS-EFC redundancy tax on a repeated repair attempt ===")
    first = NRSGates(status="passed", progress_gate=0.9, loop_gate=0.95, attempt_index=0)
    repeat = NRSGates(status="passed", progress_gate=0.9, loop_gate=0.45, attempt_index=3)
    print(f"  first attempt -> NRS-EFC_t = {nrs_efc(4.0, first):.3f}")
    print(f"  repeated fix  -> NRS-EFC_t = {nrs_efc(4.0, repeat):.3f}")

    print("\n=== 4. EFC-ADAPTER: rank candidate actions by ROI, then check the stop rule ===")
    adapter = EFCAdapter(d_task=demand.d_task, stop_threshold=0.02, window=3)
    candidates = [
        CandidateAction("verify_with_unit_test", expected_delta_efc=3.2, expected_delta_cost=1.5, verified=True),
        CandidateAction(
            "retry_same_command",
            expected_delta_efc=0.1,
            expected_delta_cost=1.2,
            verified=False,
            non_redundant=False,
        ),
        CandidateAction("route_to_specialist_tool", expected_delta_efc=2.6, expected_delta_cost=0.8, verified=True),
    ]
    ranked = adapter.rank(candidates)
    for c in ranked:
        raw_roi = c.expected_delta_efc / max(c.expected_delta_cost, 1e-9)
        print(f"  {c.action_id:26s} raw gain/cost preview = {raw_roi:.3f}")

    for c in ranked:
        adapter.retain(c, actual_efc=c.expected_delta_efc, actual_cost=c.expected_delta_cost)

    print("\n  ledger after retaining all three candidates:")
    print(adapter.ledger.to_table())
    print(f"\n  durable memory: {adapter.durable_memory}")
    print(f"  scratch space : {adapter.scratch}")
    print(f"  should_stop() after this batch: {adapter.should_stop()}")


if __name__ == "__main__":
    main()
