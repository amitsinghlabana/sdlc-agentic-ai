"""Code Reviewer agent."""
from __future__ import annotations

from ..models import WorkPackage, clip
from ..prompts import personas
from .base import Agent


class ReviewerAgent(Agent):
    id = "reviewer"
    name = "Code Reviewer"
    emoji = "🔍"
    role = "Reviews code for bugs, security, and clarity"
    system_prompt = personas.REVIEWER

    def user_prompt(self, wp: WorkPackage) -> str:
        return (
            f"Requirements:\n{clip(wp.text('requirements.md'), 1500)}\n\n"
            f"Code to review:\n{wp.code_block()}\n\n"
            "Review the code. Set verdict to 'approve' or 'request_changes' with comments."
        )

