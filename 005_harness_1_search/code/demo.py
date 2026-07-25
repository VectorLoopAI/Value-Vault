#!/usr/bin/env python3
"""
demo.py — end-to-end runnable demo of the Harness-1 reference harness.

Ties working_memory.py and reward.py together on a small toy episode so you can see the
whole loop run without a real corpus or LLM: two search calls (the second triggers
dedup), one curate + verify + promote to "very high", a budget-safe render, and a reward
score for the finished trajectory.

Usage:
    pip install pyyaml
    python3 demo.py
"""

from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from reward import RolloutOutcome, compute_reward  # noqa: E402
from working_memory import Document, WorkingMemory  # noqa: E402


def load_config() -> dict:
    cfg_path = pathlib.Path(__file__).parent.parent / "configs" / "harness_config.yaml"
    return yaml.safe_load(cfg_path.read_text())


def main() -> None:
    cfg = load_config()
    wm = WorkingMemory(cfg)

    # --- Query 1: first successful search, triggers auto-seed ---
    query1 = "When did Medea Japaridze marry her spouse?"
    raw_results = [
        Document("d1", "Medea Japaridze is an actress. She appeared in several films in the 2010s. "
                        "Her career began in Tbilisi theatre before moving to film."),
        Document("d2", "Medea Japaridze married her spouse in 2014 in a small ceremony. "
                        "The couple met on the set of a 2012 production."),
        Document("d3", "Georgian cinema saw a resurgence after 2010, with several actresses "
                        "gaining international recognition, including Medea Japaridze."),
    ]
    fresh1 = wm.ingest_search_results(query1, raw_results)
    print(f"Query 1 ingested {len(fresh1)} fresh docs; auto-seeded curated set: {wm.curated}")

    # --- Query 2: includes a near-duplicate of d2 (should be deduped) ---
    query2 = "Medea Japaridze spouse marriage date"
    raw_results_2 = [
        Document("d2-dup", "Medea Japaridze married her spouse in 2014 in a small ceremony "
                            "attended by close family. The couple met on the set of a 2012 production."),
        Document("d4", "Medea Japaridze's spouse is a film producer who also worked in Tbilisi theatre."),
    ]
    fresh2 = wm.ingest_search_results(query2, raw_results_2)
    print(f"Query 2 ingested {len(fresh2)} fresh docs (d2-dup should be filtered as a near-duplicate)")

    # --- Verify a claim against d2, then promote it to "very high" ---
    verdict = wm.verify(claim="Medea Japaridze married her spouse in 2014.", doc_ids=["d2"])
    print(f"verify() result: {verdict}")
    wm.curate("d2", action="add", importance="very high")
    print(f"Curated set after verify-before-promote: {wm.curated}")

    # --- Evidence graph + budget-safe render ---
    print("\nEvidence graph summary:")
    for k, v in wm.evidence_graph_summary().items():
        print(f"  {k}: {v}")

    print("\nBudget-safe rendered prompt state (200-token budget):")
    print(wm.render_prompt_state(token_budget=200))

    # --- Score the finished trajectory ---
    outcome = RolloutOutcome(
        curated=set(wm.curated.keys()),
        gold={"d2", "d4"},                 # ground-truth relevant docs for this toy query
        trajectory_seen=set(wm.full_text_memory.keys()),
        answer_evidence_found=True,
        answer_evidence_promoted=True,     # d2 made it into the curated set
        distinct_tools_used=3,             # fan_out_search, search_corpus, verify
        num_turns=6,
    )
    result = compute_reward(outcome, cfg)
    print(f"\nReward: {result['reward']:.4f}")
    for term, value in result["breakdown"].items():
        print(f"  {term}: {value:.4f}" if isinstance(value, float) else f"  {term}: {value}")


if __name__ == "__main__":
    main()
