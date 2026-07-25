"""
Layer 2 — Procedural Skill Layer.

Fires at task-conditioning time. Maintains a skill memory distilled from training
trajectories -- a skill being a compact, reusable strategy for a specific subtask --
retrieves the top matches for a new task by BM25 score, and injects ONLY THE TOP-1
skill into the system prompt (paper Step 2, Layer 2; script SEG 17: "across every
single experiment, only the top-1 skill is used... to keep irrelevant skills from
contaminating the context").

This module implements BM25 from scratch (no external dependency) so the whole
package stays runnable with nothing but the standard library.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class Skill:
    skill_id: str
    trigger_description: str  # what tasks this skill applies to
    strategy: str             # the actual reusable strategy text injected into the prompt


class SkillLayer:
    """A minimal, dependency-free BM25 index over a skill memory, restricted to
    top-1 retrieval per the paper's finding that a single well-matched skill beats
    several noisy ones."""

    def __init__(self, skills: Optional[List[Skill]] = None, k1: float = 1.5, b: float = 0.75):
        self.skills: List[Skill] = skills or []
        self.k1 = k1
        self.b = b
        self._doc_tokens: List[List[str]] = []
        self._doc_freqs: List[Dict[str, int]] = []
        self._df: Dict[str, int] = {}
        self._avgdl: float = 0.0
        self._rebuild_index()

    def add_skill(self, skill: Skill) -> None:
        self.skills.append(skill)
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._doc_tokens = [_tokenize(s.trigger_description) for s in self.skills]
        self._doc_freqs = []
        self._df = {}
        for tokens in self._doc_tokens:
            freqs: Dict[str, int] = {}
            for t in tokens:
                freqs[t] = freqs.get(t, 0) + 1
            self._doc_freqs.append(freqs)
            for t in freqs:
                self._df[t] = self._df.get(t, 0) + 1
        self._avgdl = (
            sum(len(t) for t in self._doc_tokens) / len(self._doc_tokens)
            if self._doc_tokens
            else 0.0
        )

    def _bm25_score(self, query_tokens: List[str], doc_index: int) -> float:
        if not self._doc_tokens:
            return 0.0
        n = len(self._doc_tokens)
        dl = len(self._doc_tokens[doc_index])
        freqs = self._doc_freqs[doc_index]
        score = 0.0
        for term in query_tokens:
            df = self._df.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            f = freqs.get(term, 0)
            denom = f + self.k1 * (1 - self.b + self.b * dl / (self._avgdl or 1))
            score += idf * (f * (self.k1 + 1)) / (denom or 1)
        return score

    def retrieve_top1(self, task_description: str) -> Optional[Skill]:
        """Return the single best-matching skill for this task, or None if the skill
        memory is empty or nothing scores above zero."""
        if not self.skills:
            return None
        query_tokens = _tokenize(task_description)
        scores = [self._bm25_score(query_tokens, i) for i in range(len(self.skills))]
        best_i = max(range(len(scores)), key=lambda i: scores[i])
        if scores[best_i] <= 0:
            return None
        return self.skills[best_i]

    def render_injection(self, task_description: str) -> str:
        """Render the top-1 skill (if any) as the exact text block to inject into the
        system prompt for this task."""
        skill = self.retrieve_top1(task_description)
        if skill is None:
            return ""
        return f"Relevant prior strategy [{skill.skill_id}]: {skill.strategy}"


if __name__ == "__main__":
    layer = SkillLayer(
        skills=[
            Skill(
                "alfworld_find_and_clean",
                "clean an object and put it somewhere, find object then clean then place",
                "Track FIND -> TAKE -> CLEAN -> GOTO_DEST -> PUT as an explicit subgoal sequence; "
                "do not repeat 'look' after the object has been located.",
            ),
            Skill(
                "webshop_compare_before_buy",
                "shop and buy an item comparing options price color size",
                "Open at least two candidate listings and compare price/attributes before "
                "clicking buy; never buy on the first search result.",
            ),
        ]
    )
    print(layer.render_injection("clean the mug and put it on the counter"))
