"""
Layer 1 — Environment Contract Layer.

Fires BEFORE interaction starts. Makes stable constraints explicit by rewriting the
model-visible contract: C' = C + delta_C, where delta_C holds concise updates derived
from environment policies, API behavior, and recurring failures observed in training
trajectories (paper Step 2, Layer 1; script SEG 16).

Targets: CONTRACT_MISMATCH failures (wrong tool, premature submission, skipped
required tool, semantically-wrong-but-schema-valid arguments).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ContractRule:
    rule: str
    text: str


@dataclass
class ContractLayer:
    """Holds the base contract C and the evolved delta_C, and renders C' = C + delta_C
    as the text block to inject into the model's system prompt."""

    base_contract: str
    delta_c: List[ContractRule] = field(default_factory=list)

    @classmethod
    def from_yaml_dict(cls, base_contract: str, delta_c_entries: list) -> "ContractLayer":
        rules = [ContractRule(rule=e["rule"], text=e["text"].strip()) for e in delta_c_entries]
        return cls(base_contract=base_contract, delta_c=rules)

    def add_rule(self, rule_id: str, text: str) -> None:
        """Called by the harness-evolution loop to append a new, local, minimal rule
        after a recurring contract-mismatch failure is diagnosed. Never edits or
        removes existing rules in place -- evolution appends, per the "local and
        minimal" evolution constraint."""
        self.delta_c.append(ContractRule(rule=rule_id, text=text))

    def render(self) -> str:
        """Produce C' as the exact text to prepend to the model's system prompt."""
        lines = [self.base_contract.strip(), "", "Additional binding rules (delta_C):"]
        for r in self.delta_c:
            lines.append(f"- [{r.rule}] {r.text}")
        return "\n".join(lines)


if __name__ == "__main__":
    layer = ContractLayer(
        base_contract="You are an agent operating tools in a deterministic environment.",
    )
    layer.add_rule(
        "flight_search_arguments",
        "The flight search tool accepts ONLY origin, destination, and date.",
    )
    layer.add_rule("passenger_cap", "A single reservation may include at most 5 passengers.")
    print(layer.render())
