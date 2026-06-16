"""Pydantic models for the knowledge/retrieval layer (provider-agnostic).

These power the **Foundry IQ** grounding feature: agentic retrieval returns
grounded text plus **citations** so agents can produce cited, grounded output
(reducing hallucination). Kept dependency-free for trivial unit testing.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """One grounded source the agents may cite as ``[S1]``, ``[S2]``, …"""

    id: str                      # short citation id, e.g. "S1"
    title: str = ""              # section / document title
    source: str = ""             # file name or knowledge-source name
    url: str = ""                # link (empty for local/mock sources)
    snippet: str = ""            # the grounded text excerpt
    score: float = 0.0           # relevance score (higher = better)


class RetrievalResult(BaseModel):
    """Result of an agentic-retrieval call."""

    query: str = ""
    citations: List[Citation] = Field(default_factory=list)
    # Sub-queries the agentic retriever planned (Foundry IQ decomposes a query).
    subqueries: List[str] = Field(default_factory=list)
    provider: str = "mock"
    # Non-empty when retrieval failed (e.g. the knowledge agent's model deployment
    # is missing). Lets the UI/test endpoint surface *why* grounding was empty.
    error: str = ""

    # -- prompt + artifact helpers ------------------------------------- #
    def as_prompt_block(self) -> str:
        """Render grounded context to inject into an agent's user prompt."""
        if not self.citations:
            return ""
        lines = [
            "Grounded knowledge (company standards — FOLLOW these and cite inline as [S#]):",
        ]
        for c in self.citations:
            label = f"[{c.id}] {c.title}".strip()
            src = f" ({c.source})" if c.source else ""
            lines.append(f"{label}{src}: {c.snippet}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Render a ``grounding.md`` artifact for the UI artifact panel."""
        if not self.citations:
            return "# Grounding\n\nNo grounded sources were retrieved."
        out = [
            "# Grounding (Foundry IQ)",
            "",
            f"Retrieved **{len(self.citations)}** source(s) to ground this run"
            f" via **{self.provider}**.",
            "",
        ]
        if self.subqueries:
            out += ["## Agentic retrieval — planned sub-queries"]
            out += [f"- {q}" for q in self.subqueries] + [""]
        out += ["## Sources"]
        for c in self.citations:
            head = f"- **[{c.id}] {c.title}**"
            if c.source:
                head += f" — `{c.source}`"
            out.append(head)
            if c.snippet:
                out.append(f"  - {c.snippet}")
        return "\n".join(out)

