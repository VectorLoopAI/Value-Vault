"""
life_harness — a reference reimplementation of the four-layer runtime harness
described in "Adapting the Interface, Not the Model" (Xu, Wen, Li — Peking University,
2026), system name LIFE-HARNESS in the paper.

This package is deliberately dependency-free (pure standard library) so it runs
anywhere, and deliberately small: it is meant to demonstrate the *pattern* --
contract injection, skill retrieval, action realization, trajectory regulation --
faithfully enough that you can lift each layer wholesale into your own agent loop.

It is NOT the authors' original code (the paper does not print a repo URL in its
body). Treat this as an independent, from-scratch implementation of the described
architecture, built for the Vector & Loop video "LLM Agent Harness: Fix the
Interface, Not the Model."
"""

from .contract_layer import ContractLayer
from .skill_layer import SkillLayer
from .action_realization_layer import ActionRealizationLayer, RealizationResult
from .trajectory_regulation_layer import TrajectoryRegulationLayer
from .pipeline import HarnessPipeline

__all__ = [
    "ContractLayer",
    "SkillLayer",
    "ActionRealizationLayer",
    "RealizationResult",
    "TrajectoryRegulationLayer",
    "HarnessPipeline",
]
