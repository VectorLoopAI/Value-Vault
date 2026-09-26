"""
acceptance_gate.py -- the weak-vs-strong acceptance rule from Autodata,
implemented once at the data level (Part 1, Agentic Self-Instruct, §3) and
once at the harness level (Part 2, meta-optimization, §4) -- deliberately
the same shape, because the paper does to its own agent exactly what its
agent does to training data.

Reference implementation from backlog/012_autodata.md; no paper repo was
public at production time. Python 3.10+ stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Part 1: per-domain data-acceptance rules
# ---------------------------------------------------------------------------

@dataclass
class SolverResult:
    """One solver's score(s) on a candidate example."""
    scores: list[float]           # per-rollout / per-attempt scores in [0, 1]

    @property
    def mean(self) -> float:
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def best(self) -> float:
        return max(self.scores) if self.scores else 0.0

    def correct_count(self, threshold: float = 0.5) -> int:
        return sum(1 for s in self.scores if s >= threshold)


def cs_acceptance(weak: SolverResult, strong: SolverResult, *,
                   strong_min: float = 0.65, weak_max: float = 0.50,
                   min_gap_pp: float = 20.0) -> dict:
    """Domain 1 (CS research questions, §3.1): fixed numeric thresholds.

    Accept only when the strong solver clears strong_min, the weak solver
    stays under weak_max, AND the gap between them is at least min_gap_pp
    percentage points. All three conditions -- not just the gap -- must hold
    (a wide gap where the strong solver also fails isn't useful either).
    """
    gap_pp = (strong.mean - weak.mean) * 100
    accepted = (
        strong.mean >= strong_min
        and weak.mean < weak_max
        and gap_pp >= min_gap_pp
    )
    return {
        "accepted": accepted,
        "weak_mean": weak.mean,
        "strong_mean": strong.mean,
        "gap_pp": gap_pp,
        "reason": None if accepted else (
            "strong solver too weak" if strong.mean < strong_min else
            "weak solver too strong (question too easy)" if weak.mean >= weak_max else
            "gap too small"
        ),
    }


def science_acceptance(weak: SolverResult, strong: SolverResult, *,
                        attempts: int = 4, weak_max_correct: int = 1,
                        strong_min_correct: int = 3,
                        correct_threshold: float = 1.0) -> dict:
    """Domain 3 (scientific reasoning, §3.3): a strict pass/fail gate over
    repeated attempts -- "zero tolerance for ambiguity." correct_threshold
    defaults to 1.0 (exact-match / verifiable answers), not a partial score.
    """
    weak_correct = weak.correct_count(correct_threshold)
    strong_correct = strong.correct_count(correct_threshold)
    accepted = weak_correct <= weak_max_correct and strong_correct >= strong_min_correct
    return {
        "accepted": accepted,
        "weak_correct": f"{weak_correct}/{attempts}",
        "strong_correct": f"{strong_correct}/{attempts}",
    }


def legal_acceptance(judge_verdict: dict) -> dict:
    """Domain 2 (legal reasoning, §3.2): NO fixed numeric threshold, by
    design -- porting the CS thresholds here would accept most of the
    broken static-generation pool, because legal's failure mode is the
    opposite of CS's (too hard, not too easy). The loop-judge asks a
    qualitative "is this GRPO-suitable?" question instead (see
    prompts/loop_judge_legal.md) and this function is intentionally a
    pass-through of that verdict, not a re-derivation of it.
    """
    return {
        "accepted": bool(judge_verdict.get("accept", False)),
        "grpo_suitability": judge_verdict.get("grpo_suitability"),
        "reason": judge_verdict.get("reasoning"),
    }


# ---------------------------------------------------------------------------
# Part 2: the harness-evolution gate -- weak vs strong, one level up
# ---------------------------------------------------------------------------

@dataclass
class RejectedMutant:
    iteration: int
    diff_description: str
    candidate_score: float
    parent_score: float

    @property
    def score_drop(self) -> float:
        return self.parent_score - self.candidate_score


@dataclass
class HarnessEvolutionGate:
    """The meta-optimizer's acceptance rule (§4): a mutant harness prompt
    survives only if its held-out validation score STRICTLY exceeds its
    parent's. Ties are rejected -- the harness never silently drifts.

    This is the exact same shape as the data-level acceptance functions
    above, one level up: instead of "strong solver beats weak solver,"
    it's "evolved harness beats baseline harness."
    """
    current_prompt: Any
    current_score: float
    best_prompt: Any = None
    best_score: float = float("-inf")
    rejected: list = field(default_factory=list)

    def __post_init__(self):
        if self.best_prompt is None:
            self.best_prompt = self.current_prompt
            self.best_score = self.current_score

    def evaluate(self, candidate_prompt: Any, candidate_score: float,
                 diff_description: str, iteration: int) -> dict:
        accepted = candidate_score > self.current_score       # strict
        new_best = accepted and candidate_score > self.best_score

        if accepted:
            self.current_prompt = candidate_prompt
            self.current_score = candidate_score
            if new_best:
                self.best_prompt = candidate_prompt
                self.best_score = candidate_score
        else:
            self.rejected.append(
                RejectedMutant(
                    iteration=iteration,
                    diff_description=diff_description,
                    candidate_score=candidate_score,
                    parent_score=self.current_score,
                )
            )

        return {
            "accepted": accepted,
            "new_best": new_best,
            "iteration": iteration,
            "current_score": self.current_score,
            "candidate_score": candidate_score,
        }


def meta_optimizer_success(weak: SolverResult, strong: SolverResult, *,
                            weak_max: float = 0.65, weak_best_max: float = 0.75,
                            strong_min: float = 0.60, strong_max: float = 0.95,
                            min_gap_pp: float = 20.0) -> bool:
    """The 4-condition definition of a "successful generated question" that
    the meta-optimizer hill-climbs on (§4) -- this is what the harness's
    validation score in HarnessEvolutionGate is actually computed FROM
    (a validation pass rate = fraction of validation papers where this
    returns True). Notice this is the CS acceptance rule from Part 1, with
    an added upper bound on the strong solver and on the weak solver's best
    attempt -- the same weak-vs-strong signal, now baked in as the reward.
    """
    gap_pp = (strong.mean - weak.mean) * 100
    return (
        weak.mean <= weak_max
        and weak.best <= weak_best_max
        and strong_min <= strong.mean <= strong_max
        and gap_pp >= min_gap_pp
    )
