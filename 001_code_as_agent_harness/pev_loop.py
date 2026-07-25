"""
Plan-Execute-Verify (PEV) loop — reference implementation.
Companion asset to Vector & Loop video 001, "Code as Agent Harness."

This is a runnable, minimal harness skeleton -- not pseudo-code. It demonstrates:

  - Plan:    a change contract (intended code + validation criteria) formed
             BEFORE any execution happens (SEG 11, SEG 15).
  - Execute: the change applied inside a permission-tiered, sandboxed
             workspace (SEG 15, SEG 16).
  - Verify:  a deterministic sensor -- a real subprocess test run, not a
             mock -- plus a human-gate stub for anything above tier 2
             (SEG 15).
  - Tool lifecycle hooks: pre-use (permission + argument validation) and
             post-use (sanitize, log, telemetry) wrapping every tool call
             (SEG 14, SEG 16).

Run it directly:

    python pev_loop.py

No external dependencies -- Python 3.9+ standard library only (tempfile,
subprocess, dataclasses, enum).

See permission_tiers.yaml in this folder for the checklist this script's
PermissionTier enum mirrors, and harness_architecture.md for the full model.
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
import tempfile
import textwrap
import time
from enum import Enum
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Permission tiers (SEG 16) -- mirrors permission_tiers.yaml in this folder.
# ---------------------------------------------------------------------------

class PermissionTier(Enum):
    READ_ONLY = 1      # browsing, retrieval, static inspection
    SANDBOX_EDIT = 2   # local patching, running tests, isolated installs
    FULL_ACCESS = 3    # network, credentials, deploy, destructive ops, git history rewrite


TIER_REQUIRES_HUMAN_GATE = {
    PermissionTier.READ_ONLY: False,
    PermissionTier.SANDBOX_EDIT: False,
    PermissionTier.FULL_ACCESS: True,   # non-negotiable per the paper (SEG 16)
}


# ---------------------------------------------------------------------------
# Telemetry (SEG 17) -- every hook call appends here; this is exactly what an
# Evolution Agent (SEG 18) would later mine offline to propose harness
# revisions.
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class TelemetryEvent:
    stage: str
    detail: str
    ts: float = dataclasses.field(default_factory=time.time)


class Telemetry:
    def __init__(self) -> None:
        self.events: List[TelemetryEvent] = []

    def log(self, stage: str, detail: str) -> None:
        self.events.append(TelemetryEvent(stage, detail))
        print(f"[telemetry] {stage:<10} | {detail}")

    def dump(self) -> str:
        return "\n".join(f"{e.stage}: {e.detail}" for e in self.events)


# ---------------------------------------------------------------------------
# Plan: the change contract (SEG 11, SEG 15, SEG 30) -- formed BEFORE
# execution, carrying its own falsification criteria and rollback path.
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ChangeContract:
    """What SEG 30 calls a 'change contract': component, target, intended
    change, and the criteria that will falsify it if unmet."""

    component: str
    target_file: str
    intended_code: str
    validation_criteria: str          # a python -c command run against the sandbox
    required_tier: PermissionTier
    rollback_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Tool lifecycle hooks (SEG 14) -- pre-use gate, then post-use sanitize/log.
# ---------------------------------------------------------------------------

def pre_use_hook(contract: ChangeContract, telemetry: Telemetry) -> None:
    telemetry.log("pre-use", f"permission check: tier={contract.required_tier.name}")
    if TIER_REQUIRES_HUMAN_GATE[contract.required_tier]:
        # In production this blocks on a real human-approval channel. The
        # demo auto-approves ONLY because execute() below refuses to run
        # FULL_ACCESS contracts at all -- see the PermissionError there.
        telemetry.log("pre-use", "HITL gate required for this tier")
    if not contract.intended_code.strip():
        raise ValueError("argument validation failed: intended_code is empty")
    telemetry.log("pre-use", "argument validation passed")


def post_use_hook(result: "ExecutionResult", telemetry: Telemetry) -> None:
    sanitized = result.stdout.strip().replace("\n", " | ")
    telemetry.log("post-use", f"sanitized output: {sanitized[:120]!r}")
    telemetry.log("post-use", f"exit_code={result.exit_code}")


# ---------------------------------------------------------------------------
# Execute: sandboxed, permission-tier-gated (SEG 15, SEG 16).
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    workspace: Path


def execute(contract: ChangeContract, telemetry: Telemetry) -> ExecutionResult:
    if contract.required_tier == PermissionTier.FULL_ACCESS:
        # Real full-access ops (deploy, git history rewrite, network calls)
        # are intentionally NOT demonstrated here -- they need a live human
        # approval channel, not a demo script. This refusal is the point,
        # not a limitation to route around.
        raise PermissionError(
            "FULL_ACCESS execution requires a live human-in-the-loop gate; "
            "refusing to proceed in this reference implementation."
        )

    workspace = Path(tempfile.mkdtemp(prefix="pev_sandbox_"))
    target = workspace / contract.target_file
    target.write_text(contract.intended_code)
    telemetry.log("execute", f"wrote {target} inside sandbox {workspace}")

    proc = subprocess.run(
        [sys.executable, "-c", contract.validation_criteria],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=10,
    )
    telemetry.log("execute", f"ran validation command, exit={proc.returncode}")
    return ExecutionResult(
        exit_code=proc.returncode,
        stdout=proc.stdout + proc.stderr,
        workspace=workspace,
    )


# ---------------------------------------------------------------------------
# Verify: deterministic sensor first, human gate stub second (SEG 15, SEG 29).
# ---------------------------------------------------------------------------

def verify(result: ExecutionResult, telemetry: Telemetry) -> bool:
    passed = result.exit_code == 0
    telemetry.log("verify", "deterministic sensor: " + ("PASS" if passed else "FAIL"))
    if not passed:
        telemetry.log(
            "verify",
            "a FAIL here is real evidence -- but per SEG 29, a PASS would only be "
            "a sample of the spec, not proof the whole spec is covered",
        )
    return passed


# ---------------------------------------------------------------------------
# The governor: Plan -> Execute -> Verify, with rollback on failure.
# ---------------------------------------------------------------------------

def run_pev_loop(contract: ChangeContract) -> bool:
    telemetry = Telemetry()
    telemetry.log("plan", f"contract formed for {contract.component} -> {contract.target_file}")

    pre_use_hook(contract, telemetry)
    result = execute(contract, telemetry)
    post_use_hook(result, telemetry)
    ok = verify(result, telemetry)

    if not ok and contract.rollback_path:
        telemetry.log("rollback", f"reverting via: {contract.rollback_path}")

    telemetry.log("done", "PASS" if ok else "FAIL")
    return ok


# ---------------------------------------------------------------------------
# Demo: a toy but real Plan-Execute-Verify pass (mirrors the SEG 15 walkthrough).
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_contract = ChangeContract(
        component="string_utils.slugify",
        target_file="string_utils.py",
        intended_code=textwrap.dedent(
            '''
            def slugify(text: str) -> str:
                return "-".join(text.lower().split())
            '''
        ),
        validation_criteria=textwrap.dedent(
            '''
            import string_utils
            assert string_utils.slugify("Code As Agent Harness") == "code-as-agent-harness"
            print("all assertions passed")
            '''
        ),
        required_tier=PermissionTier.SANDBOX_EDIT,
        rollback_path="git checkout -- string_utils.py",
    )

    success = run_pev_loop(demo_contract)
    sys.exit(0 if success else 1)
