"""Developer agent."""
from __future__ import annotations

from ..models import WorkPackage, clip
from ..prompts import personas
from .base import Agent


class DeveloperAgent(Agent):
    id = "developer"
    name = "Developer"
    emoji = "💻"
    role = "Implements the design as runnable code"
    system_prompt = personas.DEVELOPER
    emits_code = True

    def user_prompt(self, wp: WorkPackage) -> str:
        prompt = (
            f"Feature request:\n{wp.request}\n\n"
            f"Requirements:\n{clip(wp.text('requirements.md'), 2000)}\n\n"
            f"Design:\n{clip(wp.text('design.md'), 2000)}\n\n"
        )
        if wp.code_artifacts():
            prompt += f"Existing code files:\n{wp.code_block()}\n\n"
        if wp.has_context:
            prompt += (
                f"You are MODIFYING an existing repository ({wp.repo or 'the codebase'}). "
                "Edit the files above to implement the request, keeping their exact paths. "
                "Return ONLY the files you create or change (not untouched files), each with "
                "its full new content.\n\n"
            )
        if wp.review_feedback:
            bullets = "\n".join(f"- {c}" for c in wp.review_feedback)
            prompt += (
                "Reviewer feedback to address (return corrected files with the same names):\n"
                f"{bullets}\n\n"
            )
        prompt += "Implement (or revise) the code."
        return prompt

