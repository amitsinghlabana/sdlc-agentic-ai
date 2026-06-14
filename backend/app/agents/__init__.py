"""Agent team registry."""
from __future__ import annotations

from .architect import ArchitectAgent
from .base import Agent
from .developer import DeveloperAgent
from .docs import DocsAgent
from .requirements import RequirementsAgent
from .reviewer import ReviewerAgent
from .tester import TesterAgent

# Display/handoff order for the pipeline.
TEAM_ORDER = ["requirements", "architect", "developer", "tester", "reviewer", "docs"]


def build_team() -> "dict[str, Agent]":
    return {
        "requirements": RequirementsAgent(),
        "architect": ArchitectAgent(),
        "developer": DeveloperAgent(),
        "tester": TesterAgent(),
        "reviewer": ReviewerAgent(),
        "docs": DocsAgent(),
    }


def team_roster() -> list[dict]:
    """Lightweight metadata for the UI."""
    team = build_team()
    return [
        {"id": a.id, "name": a.name, "emoji": a.emoji, "role": a.role}
        for a in (team[k] for k in TEAM_ORDER)
    ]

