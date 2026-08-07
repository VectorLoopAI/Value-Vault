"""
skill_patch.py — bounded patch-mode edits on a SKILL.md-style document
(SkillOpt §3.4). Patch mode is the paper's default edit mode: localized
append / insert_after / replace / delete operations that touch only the
lines an edit names, as opposed to `rewrite_from_suggestions` (a full
rewrite), which the paper's ablation shows is worse than any bounded
budget (§4.2, "without lr").
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SkillDocument:
    """A skill file as an ordered list of addressable rules, so patch ops
    can target a specific rule by id without touching the rest of the
    document — the property the paper calls "preserving continuity."
    """

    rules: list = field(default_factory=list)  # [{"id": str, "text": str}, ...]
    protected_ids: set = field(default_factory=set)
    _next_id: int = 1

    @classmethod
    def from_lines(cls, lines: list[str]) -> "SkillDocument":
        doc = cls()
        for line in lines:
            doc.rules.append({"id": f"R{doc._next_id}", "text": line})
            doc._next_id += 1
        return doc

    def _index(self, rule_id: str) -> int:
        for i, r in enumerate(self.rules):
            if r["id"] == rule_id:
                return i
        raise KeyError(f"no rule with id {rule_id!r}")

    def apply(self, edits: list[dict]) -> "SkillDocument":
        """Apply a list of patch ops in order, respecting the SLOW_UPDATE
        protection rule (§3.6): no step-level edit may target a rule whose
        id is in `self.protected_ids`.
        """
        for edit in edits:
            op = edit["op"]
            target = edit.get("target_id")
            if target is not None and target in self.protected_ids:
                raise PermissionError(
                    f"edit targets protected rule {target!r} "
                    "(SLOW_UPDATE block is off-limits to step-level edits)"
                )
            if op == "append":
                self.rules.append({"id": f"R{self._next_id}", "text": edit["text"]})
                self._next_id += 1
            elif op == "insert_after":
                idx = self._index(target)
                self.rules.insert(idx + 1, {"id": f"R{self._next_id}", "text": edit["text"]})
                self._next_id += 1
            elif op == "replace":
                idx = self._index(target)
                self.rules[idx]["text"] = edit["text"]
            elif op == "delete":
                idx = self._index(target)
                del self.rules[idx]
            else:
                raise ValueError(f"unknown patch op: {op!r}")
        return self

    def clone(self) -> "SkillDocument":
        new = SkillDocument(
            rules=[dict(r) for r in self.rules],
            protected_ids=set(self.protected_ids),
        )
        new._next_id = self._next_id
        return new

    def to_markdown(self) -> str:
        return "\n".join(f"- ({r['id']}) {r['text']}" for r in self.rules)

    def token_estimate(self) -> int:
        """Rough token count (~1.3 tokens/word) purely for the compactness
        sanity-check in the README — not the paper's own tokenizer.
        """
        words = sum(len(r["text"].split()) for r in self.rules)
        return round(words * 1.3)


if __name__ == "__main__":
    doc = SkillDocument.from_lines(["Inspect workbook structure and formulas before answering."])
    doc.apply(
        [
            {
                "op": "append",
                "text": "Write evaluated static values instead of leaving formulas for the grader to recalculate.",
            }
        ]
    )
    print(doc.to_markdown())
    print(f"estimated tokens: {doc.token_estimate()}")
