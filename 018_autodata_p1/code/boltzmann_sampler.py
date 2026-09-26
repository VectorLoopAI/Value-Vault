"""
boltzmann_sampler.py -- parent selection for the meta-optimizer's
population-based prompt evolution (Autodata §4).

P(select candidate i) is proportional to exp(score_i / T). Low T (paper
uses T=0.1) strongly favors high-scoring candidates while still,
occasionally, sampling a weaker one -- so the search doesn't collapse onto
a single lineage too early. Multiple concurrent iterations each pick a
parent independently, so this is a branching population, not a single
ladder.

Reference implementation from backlog/012_autodata.md. Python 3.10+ stdlib
only.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Candidate:
    id: str
    prompt: object
    score: float          # running average across all re-evaluations (§4:
                           # solvers run at T=1.0, so scores are noisy --
                           # accepted candidates accumulate more evaluations
                           # whenever re-sampled, and the reported score is
                           # the average across all of them)


def boltzmann_weights(candidates: list[Candidate], temperature: float = 0.1) -> list[float]:
    """Numerically stable softmax over candidate scores at the given
    temperature. Returns normalized selection probabilities in the same
    order as `candidates`.
    """
    if not candidates:
        return []
    max_score = max(c.score for c in candidates)
    exp_vals = [math.exp((c.score - max_score) / temperature) for c in candidates]
    total = sum(exp_vals)
    return [v / total for v in exp_vals]


def select_parent(candidates: list[Candidate], temperature: float = 0.1,
                   rng: random.Random | None = None) -> Candidate:
    """Sample one parent candidate via Boltzmann selection."""
    rng = rng or random
    weights = boltzmann_weights(candidates, temperature)
    return rng.choices(candidates, weights=weights, k=1)[0]


def record_reevaluation(candidate: Candidate, new_score: float, prior_evals: int) -> Candidate:
    """When an accepted candidate is re-sampled as a parent later, it picks
    up another evaluation; the paper reports the running average across all
    evaluations rather than the latest (noisy) single sample. `prior_evals`
    is how many evaluations already went into `candidate.score`.
    """
    total_evals = prior_evals + 1
    averaged = (candidate.score * prior_evals + new_score) / total_evals
    return Candidate(id=candidate.id, prompt=candidate.prompt, score=averaged)


if __name__ == "__main__":
    # Tiny illustration: a population where one candidate is clearly ahead
    # but the low-temperature sampler still occasionally explores others.
    pop = [
        Candidate("baseline", prompt="...", score=0.621),
        Candidate("mutant_a", prompt="...", score=0.681),
        Candidate("mutant_b", prompt="...", score=0.796),
    ]
    weights = boltzmann_weights(pop, temperature=0.1)
    for c, w in zip(pop, weights):
        print(f"{c.id:>10}  score={c.score:.3f}  P(select)={w:.4f}")
