"""
HarnessPipeline — wires all four LIFE-HARNESS layers around a single agent step, and
a runnable demo (`python -m life_harness.pipeline`) that fires every layer at least
once against the toy DemoEnv, so you can see the whole loop from Algorithm 1 (paper)
/ SEG 16-19 (script) in ~100 lines with no benchmark install required.

Order of operations per step, matching the paper's lifecycle:
    0. (once, before interaction) Environment Contract Layer renders C' for the
       system prompt.
    1. (per task) Procedural Skill Layer retrieves the top-1 skill and injects it.
    2. model proposes an action (in this demo: a scripted stand-in, since no model
       weights ship with this repo).
    3. Action Realization Layer validates / canonicalizes / blocks before execution.
    4. environment executes (or the block message is returned to the model instead).
    5. Trajectory Regulation Layer inspects the running trajectory and may escalate
       a message on top of the environment's own feedback.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .action_realization_layer import ActionRealizationLayer, ToolSchema
from .contract_layer import ContractLayer
from .demo_env import DemoEnv
from .skill_layer import Skill, SkillLayer
from .trajectory_regulation_layer import TrajectoryRegulationLayer


class HarnessPipeline:
    def __init__(
        self,
        contract_layer: ContractLayer,
        skill_layer: SkillLayer,
        action_layer: ActionRealizationLayer,
        regulation_layer: TrajectoryRegulationLayer,
    ):
        self.contract_layer = contract_layer
        self.skill_layer = skill_layer
        self.action_layer = action_layer
        self.regulation_layer = regulation_layer

    def system_prompt(self, task_description: str) -> str:
        """Everything the model sees before choosing an action this task: the
        contract-augmented system prompt (Layer 1) plus the top-1 retrieved skill
        (Layer 2)."""
        parts = [self.contract_layer.render()]
        skill_text = self.skill_layer.render_injection(task_description)
        if skill_text:
            parts.append(skill_text)
        return "\n\n".join(parts)

    def step(
        self,
        raw_model_output: str,
        tool_name: Optional[str],
        parsed_args: Optional[Dict[str, Any]],
        trajectory: List[Any],
    ):
        """Runs Layer 3 (action realization) then, on success, returns the
        canonicalized executable action. Layer 4 (trajectory regulation) is applied
        separately via `regulate()` after the environment step, since it needs the
        environment's feedback first."""
        return self.action_layer.realize(raw_model_output, tool_name, parsed_args, trajectory)

    def regulate(self):
        return self.regulation_layer.regulate()


def _demo() -> None:
    # --- Layer 1: contract -----------------------------------------------------
    contract = ContractLayer(base_contract="You are an agent operating tools in ALFWorld.")
    contract.add_rule(
        "no_repeat_look",
        "Do not call 'look' twice in a row without an intervening action that changes state.",
    )

    # --- Layer 2: skill memory ---------------------------------------------------
    skills = SkillLayer(
        skills=[
            Skill(
                "find_take_goto_put",
                "put an object somewhere, take object then go then put",
                "Sequence: find object -> take -> goto destination -> put. Do not repeat "
                "'look' once the object's location is known.",
            )
        ]
    )

    # --- Layer 3: action realization ---------------------------------------------
    actions = ActionRealizationLayer(
        [
            ToolSchema(name="take", required_args=["object"]),
            ToolSchema(name="goto", required_args=["destination"]),
            ToolSchema(name="put", required_args=["object", "destination"]),
            ToolSchema(name="look", required_args=[]),
        ]
    )

    # --- Layer 4: trajectory regulation --------------------------------------------
    regulation = TrajectoryRegulationLayer(step_budget=10)

    pipeline = HarnessPipeline(contract, skills, actions, regulation)

    task = "put the mug on the counter"
    print("=== System prompt for this task (Layers 1+2) ===")
    print(pipeline.system_prompt(task))
    print()

    env = DemoEnv(task=task)
    trajectory: List[Any] = []

    # A scripted "frozen model" that repeats 'look' a few times before acting --
    # reproducing the trajectory-degeneration shape from ALFWorld (SEG 13/19).
    scripted_actions = [
        {"tool": "look", "args": {}},
        {"tool": "look", "args": {}},
        {"tool": "look", "args": {}},
        # A malformed action realization case: missing required arg.
        {"tool": "take", "args": {}},
        # Corrected on the next "turn" after the block message:
        {"tool": "take", "args": {"object": "mug"}},
        {"tool": "goto", "args": {"destination": "counter"}},
        {"tool": "put", "args": {"object": "mug", "destination": "counter"}},
    ]

    print("=== Step-by-step trace ===")
    for raw in scripted_actions:
        result = pipeline.step(
            raw_model_output=str(raw), tool_name=raw["tool"], parsed_args=raw["args"], trajectory=trajectory
        )
        if not result.executable:
            print(f"[Layer 3 BLOCK] proposed={raw} -> {result.block_message}")
            continue

        obs, made_progress, done = env.step(result.action)
        state_signature = (env.location, tuple(sorted(env.holding)))
        regulation.record_step(action=result.action["tool"], state_signature=state_signature, made_progress=made_progress)
        trajectory.append({"action": result.action, "observation": obs})

        reg_result = pipeline.regulate()
        line = f"[executed] {result.action} -> {obs!r}"
        if reg_result.tier != "none":
            line += f"  | [Layer 4 {reg_result.tier}] {reg_result.message}"
        print(line)

        if done:
            print("Task complete.")
            break


if __name__ == "__main__":
    _demo()
