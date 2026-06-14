"""Architect agent."""
from __future__ import annotations

from ..models import WorkPackage, clip
from ..prompts import personas
from .base import Agent


class ArchitectAgent(Agent):
    id = "architect"
    name = "Architect"
    emoji = "🏛️"
    role = "Designs the solution, stack, and API contract"
    system_prompt = personas.ARCHITECT

    def user_prompt(self, wp: WorkPackage) -> str:
        return wp.with_grounding(
            f"Feature request:\n{wp.request}\n\n"
            f"Approved requirements:\n{clip(wp.text('requirements.md'))}\n\n"
            "Produce the technical design (design.md)."
        )

