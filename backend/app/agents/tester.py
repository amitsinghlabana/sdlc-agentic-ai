"""Tester / QA agent."""
from __future__ import annotations

from ..models import WorkPackage, clip
from ..prompts import personas
from .base import Agent


class TesterAgent(Agent):
    id = "tester"
    name = "Tester / QA"
    emoji = "🧪"
    role = "Writes unit tests for the implementation"
    system_prompt = personas.TESTER
    emits_code = True

    def user_prompt(self, wp: WorkPackage) -> str:
        return (
            f"Requirements:\n{clip(wp.text('requirements.md'), 1500)}\n\n"
            f"Code under test:\n{wp.code_block()}\n\n"
            "Write focused unit tests (happy path + at least one failure path)."
        )

