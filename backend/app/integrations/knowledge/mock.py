"""Free, offline, deterministic knowledge client — the default provider.

Reads the in-repo standards docs (``docs/standards/*.md``), splits them into
sections by ``##`` headings, and returns the best-matching sections as
**citations** using simple keyword overlap. Zero cost, no account, fully
offline — mirroring ``MockJiraClient`` / ``MockProvider`` so the whole Foundry
IQ grounding feature is demoable and testable without Azure.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .base import KnowledgeClient
from .models import Citation, RetrievalResult

# Tiny built-in fallback so retrieval still works if no docs dir is present.
_FALLBACK = [
    ("Password storage", "security-checklist.md",
     "Passwords must never be stored or compared in plaintext; hash with bcrypt/scrypt/Argon2id."),
    ("Input validation", "security-checklist.md",
     "Validate and sanitize all input server-side; reject malformed payloads with 400."),
    ("Story format", "story-writing-conventions.md",
     "Use 'As a <role>, I want <goal> so that <benefit>'; summaries under 255 chars."),
]

_STOP = {
    "the", "a", "an", "to", "of", "and", "or", "for", "in", "on", "with", "is",
    "are", "be", "can", "i", "we", "as", "so", "that", "this", "it", "add", "build",
}


def _keywords(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", (text or "").lower())
    return [w for w in words if w not in _STOP]


class MockKnowledgeClient(KnowledgeClient):
    name = "mock"
    label = "Mock (free)"

    def __init__(self, knowledge_dir: str = "") -> None:
        self._dir = Path(knowledge_dir) if knowledge_dir else None
        self._sections = self._load()

    # ------------------------------------------------------------------ #
    def _load(self) -> List[tuple[str, str, str]]:
        """Return a list of (title, source_filename, text) sections."""
        sections: List[tuple[str, str, str]] = []
        if self._dir and self._dir.exists():
            for md in sorted(self._dir.glob("*.md")):
                text = md.read_text(encoding="utf-8", errors="ignore")
                # Split on '##' headings; keep heading as the section title.
                parts = re.split(r"^##\s+", text, flags=re.M)
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    line, _, body = part.partition("\n")
                    title = line.strip()
                    body = " ".join(body.split())
                    if title and body:
                        sections.append((title, md.name, body))
        return sections or list(_FALLBACK)

    @property
    def sources_count(self) -> int:
        return len(self._sections)

    def _snippet(self, text: str, limit: int = 240) -> str:
        return text if len(text) <= limit else text[:limit].rstrip() + "…"

    async def retrieve(self, query: str, *, top: int = 5) -> RetrievalResult:
        terms = set(_keywords(query))
        scored: List[tuple[int, int, tuple[str, str, str]]] = []
        for idx, sec in enumerate(self._sections):
            title, _src, body = sec
            haystack = f"{title} {body}".lower()
            score = sum(haystack.count(t) for t in terms)
            # idx as a stable tie-breaker → deterministic ordering.
            scored.append((score, -idx, sec))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        # Standard top-K retrieval: matched sections rank first; if too few matched,
        # the next best (related) sections fill the panel for richer grounding.
        matched = [s for s in scored if s[0] > 0]
        chosen = matched[:top] if len(matched) >= top else (matched + [s for s in scored if s[0] == 0])[:top]

        citations: List[Citation] = []
        for i, (score, _tie, (title, src, body)) in enumerate(chosen, start=1):
            citations.append(
                Citation(
                    id=f"S{i}", title=title, source=src,
                    snippet=self._snippet(body), score=float(max(score, 0)),
                )
            )

        # Deterministic "agentic" sub-queries derived from the top keywords.
        kw = sorted(terms)[:3]
        subqueries = [f"standards relevant to '{k}'" for k in kw] or ["relevant engineering standards"]

        return RetrievalResult(
            query=query, citations=citations, subqueries=subqueries, provider=self.name
        )


