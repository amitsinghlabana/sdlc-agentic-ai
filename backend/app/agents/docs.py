"""Documentation agent."""
from __future__ import annotations

from ..models import WorkPackage, clip
from ..prompts import personas
from .base import Agent


class DocsAgent(Agent):
    id = "docs"
    name = "Documentation"
    emoji = "📚"
    role = "Writes the feature README"
    system_prompt = personas.DOCS

    def user_prompt(self, wp: WorkPackage) -> str:
        files = ", ".join(a.name for a in wp.code_artifacts()) or "(none)"
        return (
            f"Feature request:\n{wp.request}\n\n"
            f"Requirements:\n{clip(wp.text('requirements.md'), 1200)}\n\n"
            f"Design:\n{clip(wp.text('design.md'), 1200)}\n\n"
            f"Implemented files: {files}\n\n"
            "Write a concise README section (overview, run, API, tests)."
        )

