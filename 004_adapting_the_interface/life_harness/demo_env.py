"""
A tiny, deterministic, dependency-free toy environment used only to demonstrate the
four harness layers firing end-to-end (`python -m life_harness.pipeline`). It is NOT
ALFWorld, tau-bench, or DBBench -- it is a minimal stand-in that reproduces the two
failure shapes discussed in the video: a DBBench-style malformed/invalid tool call,
and an ALFWorld-style repeated-action loop. Swap this out for a real benchmark's
`step()` function and the harness code is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DemoEnv:
    task: str = "put the mug on the counter"
    location: str = "start_room"
    holding: List[str] = field(default_factory=list)
    steps_taken: int = 0
    done: bool = False

    def step(self, action: Dict[str, Any]):
        """Returns (observation: str, made_progress: bool, done: bool)."""
        self.steps_taken += 1
        tool = action.get("tool")
        args = action.get("args", {})

        if tool == "take":
            obj = args.get("object")
            if obj and obj not in self.holding:
                self.holding.append(obj)
                return (f"You pick up the {obj}.", True, False)
            return ("Nothing happens.", False, False)

        if tool == "goto":
            dest = args.get("destination")
            if dest and dest != self.location:
                self.location = dest
                return (f"You move to {dest}.", True, False)
            return ("Nothing happens.", False, False)

        if tool == "put":
            obj = args.get("object")
            dest = args.get("destination")
            if obj in self.holding and dest == self.location:
                self.holding.remove(obj)
                self.done = True
                return (f"You place the {obj} on {dest}. Task complete.", True, True)
            return ("Nothing happens.", False, False)

        if tool == "look":
            return (f"You are in {self.location}. Holding: {self.holding or 'nothing'}.", False, False)

        return ("Unrecognized action.", False, False)
