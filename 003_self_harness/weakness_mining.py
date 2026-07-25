"""
weakness_mining.py — Self-Harness Stage 1: Weakness Mining.

Clusters failed execution traces by a failure signature phi(r_i) = (c_i, q_i, m_i):
    c_i - terminal verifier-level cause (e.g. "timeout", "missing_artifact")
    q_i - causal status of the agent's own behavior that led there
    m_i - the abstract, reusable agent mechanism the trace exposed

Two failures are only grouped into the same cluster if they agree on ALL THREE
fields — this is what prevents two superficially-identical failures (e.g. two
"timeout" traces with unrelated root causes) from being conflated into one
bogus, unfixable pattern.

Output is an "evidence bundle": ranked, structured failure clusters. This stage
deliberately stops short of proposing any fix — diagnosis is kept separate
from treatment (that's Stage 2, harness proposal).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FailureSignature:
    """phi(r_i) = (c_i, q_i, m_i)"""
    cause: str          # c_i: terminal verifier-level cause
    behavior: str       # q_i: causal status of agent behavior
    mechanism: str      # m_i: abstract mechanism exposed

    def key(self) -> tuple[str, str, str]:
        return (self.cause, self.behavior, self.mechanism)


@dataclass
class Trace:
    task_id: str
    signature: FailureSignature
    notes: str = ""


@dataclass
class Cluster:
    signature: FailureSignature
    traces: list[Trace] = field(default_factory=list)

    @property
    def support(self) -> int:
        return len(self.traces)

    def actionability_score(self) -> float:
        """
        Placeholder heuristic for "estimated actionability" (paper leaves the
        exact scoring function unspecified). Traces with a non-generic
        mechanism (not "task_difficulty" / "capability_limit") are treated as
        actionable; those two mechanism labels are excluded downstream in
        Stage 2 rather than force-patched, matching the paper's caveat that
        not every cluster gets a proposal.
        """
        if self.signature.mechanism in ("task_difficulty", "capability_limit"):
            return 0.0
        return float(self.support)


def mine_weaknesses(traces: list[Trace]) -> list[Cluster]:
    """Stage 1: cluster failed traces into an evidence bundle, ranked."""
    clusters: dict[tuple[str, str, str], Cluster] = {}
    for t in traces:
        key = t.signature.key()
        if key not in clusters:
            clusters[key] = Cluster(signature=t.signature)
        clusters[key].traces.append(t)

    ranked = sorted(
        clusters.values(),
        key=lambda c: (c.actionability_score(), c.support),
        reverse=True,
    )
    return ranked


def print_evidence_bundle(clusters: list[Cluster]) -> None:
    print(f"Evidence bundle: {len(clusters)} cluster(s)\n")
    for i, c in enumerate(clusters, 1):
        s = c.signature
        print(f"[{i}] cause={s.cause!r} behavior={s.behavior!r} mechanism={s.mechanism!r}")
        print(f"    support={c.support}  actionability={c.actionability_score()}")
        for t in c.traces:
            print(f"      - {t.task_id}: {t.notes}")
        print()


if __name__ == "__main__":
    # Sample traces modeled on the video's own case studies (extract-elf,
    # count-dataset-tokens, build-pov-ray) plus the "two unrelated timeouts"
    # example used to explain why the signature needs all three fields.
    sample_traces = [
        Trace(
            "extract-elf-run-1",
            FailureSignature("missing_artifact", "self_deleted_required_file", "no_error_recovery_policy"),
            notes="Agent hit repeated edit failures, then deleted /app/extract.js itself.",
        ),
        Trace(
            "count-dataset-tokens-run-1",
            FailureSignature("timeout", "over_exploration_after_goal_found", "no_early_artifact_creation"),
            notes="Kept exploring after finding the needed metadata config; never wrote answer.txt.",
        ),
        Trace(
            "build-pov-ray-run-1",
            FailureSignature("verifier_reject", "rationalized_failing_checks", "no_explore_to_implement_gate"),
            notes="Burned budget on monolithic downloads, finalized despite failing sanity checks.",
        ),
        # The "two unrelated timeouts" illustration from the video (SEG 10):
        # same terminal cause (timeout), different (q, m) -> stay separate clusters.
        Trace(
            "timeout-A",
            FailureSignature("timeout", "looping_on_broken_tool_call", "no_error_recovery_policy"),
            notes="Timed out looping on a broken tool call.",
        ),
        Trace(
            "timeout-B",
            FailureSignature("timeout", "mid_large_download", "no_dependency_precheck"),
            notes="Timed out mid-download of a large dependency.",
        ),
    ]

    bundle = mine_weaknesses(sample_traces)
    print_evidence_bundle(bundle)
