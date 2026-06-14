"""Abstract knowledge/retrieval client contract (mirrors ``llm/base.py`` and
``jira/base.py``).

Implementations provide **agentic retrieval**: given a query, return grounded
citations the agents can cite. This is the seam where **Foundry IQ** plugs in.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import RetrievalResult


class KnowledgeClient(ABC):
    name: str = "base"
    # Human-readable label shown in the UI badge (e.g. "Mock (free)").
    label: str = "Base"

    @abstractmethod
    async def retrieve(self, query: str, *, top: int = 5) -> RetrievalResult:
        """Return grounded citations for ``query`` (best-effort, never raises)."""
        raise NotImplementedError

