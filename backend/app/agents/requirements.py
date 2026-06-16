"""Requirements Analyst agent."""
from __future__ import annotations

from ..models import WorkPackage
from ..prompts import personas
from .base import Agent


class RequirementsAgent(Agent):
    id = "requirements"
    name = "Requirements Analyst"
    emoji = "📝"
    role = "Turns the request into user stories + acceptance criteria"
    system_prompt = personas.REQUIREMENTS
    # Emits requirements.md + a structured stories.json (with sub-tasks); use the
    # larger token budget so the second artifact isn't truncated away.
    large_output = True

    def user_prompt(self, wp: WorkPackage) -> str:
        return wp.with_grounding(
            f"Feature request:\n{wp.request}\n\nProduce the requirements."
        )

