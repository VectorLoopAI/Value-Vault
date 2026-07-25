"""
Layer 3 — Action Realization Layer.

Sits between the model's proposed action and execution. Computes
RealizeAction(action, trajectory, state) -> Exec(action) | Block(message), using
deterministic environment evidence (tool schemas, admissible action sets, argument
constraints, task policies) to (paper Step 2, Layer 3; script SEG 18):

  1. Validate the action against the tool schema / admissible-action set.
  2. Canonicalize unambiguous interface-level errors (fix the malformed thing when the
     fix is obvious -- e.g. strip stray backticks, coerce a quoted-number string).
  3. Block actions that would deterministically fail, returning a model-visible block
     message so the model can course-correct on its next turn.

Targets: ACTION_REALIZATION failures.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolSchema:
    name: str
    required_args: List[str] = field(default_factory=list)
    # optional per-argument validators, e.g. {"amount": lambda v: isinstance(v, (int, float))}
    arg_validators: Dict[str, Callable[[Any], bool]] = field(default_factory=dict)
    # optional guard(action_dict, trajectory) -> Optional[str]; returns a block message
    # if the guard fails, or None if the action is fine. Used for business-rule guards
    # like the Airline book_reservation checks in configs/example_airline_contract.yaml.
    guards: List[Callable[[Dict[str, Any], list], Optional[str]]] = field(default_factory=list)


@dataclass
class RealizationResult:
    executable: bool
    action: Optional[Dict[str, Any]]   # canonicalized action, if executable
    block_message: Optional[str]       # model-visible message, if blocked
    canonicalized: bool = False        # True if the action was auto-repaired


class ActionRealizationLayer:
    """Deterministic pre-execution gate. Holds a registry of ToolSchema objects and
    applies validate -> canonicalize -> guard-check, in that order, to every proposed
    action before it reaches the environment's step function."""

    def __init__(self, tool_schemas: Optional[List[ToolSchema]] = None):
        self.schemas: Dict[str, ToolSchema] = {s.name: s for s in (tool_schemas or [])}

    def register_tool(self, schema: ToolSchema) -> None:
        self.schemas[schema.name] = schema

    # -- canonicalization helpers -------------------------------------------------

    @staticmethod
    def _strip_markdown_fencing(raw: str) -> str:
        """Common near-miss: the model wraps a tool call in markdown code fences or
        stray backticks. Strip them -- this is the 'automatic backtick repair'
        described for the OS/DBBench harness in the video (SEG 24)."""
        cleaned = raw.strip()
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        return cleaned.strip("` \n")

    @staticmethod
    def _try_parse_json_ish(raw: str) -> Optional[Dict[str, Any]]:
        """Attempt to canonicalize a near-JSON tool call (single quotes, trailing
        commas, unquoted keys) into valid JSON before giving up and blocking."""
        candidate = raw
        # unquoted keys: {name: "x"} -> {"name": "x"}
        candidate = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', candidate)
        # single-quoted strings -> double-quoted
        candidate = re.sub(r"'([^']*)'", r'"\1"', candidate)
        # trailing commas before } or ]
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    def realize(
        self,
        raw_model_output: str,
        tool_name: Optional[str],
        parsed_args: Optional[Dict[str, Any]],
        trajectory: Optional[list] = None,
    ) -> RealizationResult:
        trajectory = trajectory or []

        # Step 1: does the named tool even exist?
        if tool_name is None or tool_name not in self.schemas:
            # Try to canonicalize: strip fencing and re-parse as {"tool": ..., "args": ...}
            cleaned = self._strip_markdown_fencing(raw_model_output)
            parsed = self._try_parse_json_ish(cleaned)
            if parsed and "tool" in parsed and parsed["tool"] in self.schemas:
                return self.realize(
                    raw_model_output, parsed["tool"], parsed.get("args", {}), trajectory
                )
            return RealizationResult(
                executable=False,
                action=None,
                block_message=(
                    f"Action realization failed: '{tool_name or raw_model_output[:60]}' is not "
                    f"a recognized tool. Valid tools: {sorted(self.schemas.keys())}."
                ),
            )

        schema = self.schemas[tool_name]
        args = dict(parsed_args or {})
        canonicalized = False

        # Step 2: canonicalize obviously-fixable argument issues (e.g. "5" -> 5 for a
        # numeric arg the schema expects).
        for arg_name, validator in schema.arg_validators.items():
            if arg_name in args and not validator(args[arg_name]):
                value = args[arg_name]
                if isinstance(value, str) and value.strip().lstrip("-").isdigit():
                    args[arg_name] = int(value.strip())
                    canonicalized = True

        # Step 3: required-argument check (interface-level, cannot be auto-fixed).
        missing = [a for a in schema.required_args if a not in args]
        if missing:
            return RealizationResult(
                executable=False,
                action=None,
                block_message=(
                    f"Action realization failed: tool '{tool_name}' is missing required "
                    f"argument(s) {missing}. Re-emit the call with all required arguments."
                ),
                canonicalized=canonicalized,
            )

        # Step 4: re-validate arguments after canonicalization.
        for arg_name, validator in schema.arg_validators.items():
            if arg_name in args and not validator(args[arg_name]):
                return RealizationResult(
                    executable=False,
                    action=None,
                    block_message=(
                        f"Action realization failed: argument '{arg_name}' for tool "
                        f"'{tool_name}' failed validation (value={args[arg_name]!r})."
                    ),
                    canonicalized=canonicalized,
                )

        # Step 5: business-rule / contract guards (e.g. duplicate payment ID).
        for guard in schema.guards:
            message = guard({"tool": tool_name, **args}, trajectory)
            if message:
                return RealizationResult(
                    executable=False, action=None, block_message=message, canonicalized=canonicalized
                )

        return RealizationResult(
            executable=True,
            action={"tool": tool_name, "args": args},
            block_message=None,
            canonicalized=canonicalized,
        )


if __name__ == "__main__":
    layer = ActionRealizationLayer(
        [
            ToolSchema(
                name="book_reservation",
                required_args=["flight_number", "payment_id", "amount"],
                arg_validators={"amount": lambda v: isinstance(v, (int, float))},
            )
        ]
    )
    # A malformed-but-recoverable call: amount comes in as a string.
    result = layer.realize(
        raw_model_output="",
        tool_name="book_reservation",
        parsed_args={"flight_number": "AA100", "payment_id": "pm_1", "amount": "250"},
    )
    print(result)
