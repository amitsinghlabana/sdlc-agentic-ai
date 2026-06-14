"""Shared data models (the "work package" that flows between agents)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Artifact(BaseModel):
    """A single produced file or document."""

    name: str  # e.g. "requirements.md" or "app/auth.py"
    type: str = "markdown"  # markdown | code | test | config | doc
    language: str = "markdown"  # python | markdown | html | yaml | ...
    content: str = ""


class AgentResult(BaseModel):
    """Structured output returned by every agent."""

    agent_id: str
    agent_name: str
    emoji: str = "🤖"
    summary: str = ""
    details: str = ""
    artifacts: List[Artifact] = Field(default_factory=list)
    # Reviewer-only fields
    verdict: Optional[str] = None  # "approve" | "request_changes"
    comments: List[str] = Field(default_factory=list)
    # Optional advisory note (e.g. "response was truncated; recovered N files").
    note: Optional[str] = None


def clip(text: str, limit: int = 4000) -> str:
    """Trim long artifact content before stuffing it into a prompt (token guard)."""
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated] ..."


# Extension → (type, language) for files read back from an existing repo.
_EXT_MAP: dict[str, tuple[str, str]] = {
    ".py": ("code", "python"), ".js": ("code", "javascript"), ".jsx": ("code", "javascript"),
    ".mjs": ("code", "javascript"), ".cjs": ("code", "javascript"),
    ".ts": ("code", "typescript"), ".tsx": ("code", "typescript"),
    ".html": ("code", "html"), ".htm": ("code", "html"), ".css": ("code", "css"),
    ".json": ("config", "json"), ".yaml": ("config", "yaml"), ".yml": ("config", "yaml"),
    ".toml": ("config", "toml"), ".ini": ("config", "ini"), ".cfg": ("config", "ini"),
    ".md": ("doc", "markdown"), ".markdown": ("doc", "markdown"), ".txt": ("doc", "text"),
    ".java": ("code", "java"), ".go": ("code", "go"), ".rb": ("code", "ruby"),
    ".rs": ("code", "rust"), ".php": ("code", "php"), ".cs": ("code", "csharp"),
    ".sh": ("code", "bash"), ".sql": ("code", "sql"),
}


def _is_test_path(path: str) -> bool:
    p = path.lower()
    base = p.rsplit("/", 1)[-1]
    return (
        base.startswith("test_")
        or base.endswith("_test.py")
        or ".test." in base
        or ".spec." in base
        or "/tests/" in p
        or "/test/" in p
        or "/__tests__/" in p
    )


def infer_artifact(path: str, content: str = "") -> "Artifact":
    """Build an Artifact from a file path, inferring its type + language.

    Used when reading existing repository files into the pipeline as context.
    """
    ext = ""
    base = path.rsplit("/", 1)[-1]
    if "." in base:
        ext = "." + base.rsplit(".", 1)[-1].lower()
    type_, language = _EXT_MAP.get(ext, ("code", "text"))
    if _is_test_path(path) and type_ == "code":
        type_ = "test"
    return Artifact(name=path, type=type_, language=language, content=content)


class WorkPackage:
    """Mutable, in-run shared state passed down the agent pipeline."""

    def __init__(self, request: str) -> None:
        self.request: str = request
        self.artifacts: "dict[str, Artifact]" = {}
        self.history: List[AgentResult] = []
        self.review_feedback: List[str] = []
        # Foundry IQ grounding: a prompt-ready block + the citations behind it.
        self.grounding_block: str = ""
        self.citations: List[dict] = []
        # Existing repository files loaded as READ-ONLY context (not published).
        # The Developer/Tester see these as "existing code" to edit in place.
        self.context_files: "dict[str, Artifact]" = {}
        self.repo: Optional[str] = None  # the repo being edited, when applicable

    # --- grounding helper ---
    def with_grounding(self, prompt: str) -> str:
        """Prepend retrieved, citable company standards (if any) to a prompt."""
        if not self.grounding_block:
            return prompt
        return (
            f"{self.grounding_block}\n\n"
            "Use the grounded sources above where relevant and cite them inline "
            "like [S1]. Do not invent standards that contradict them.\n\n"
            f"{prompt}"
        )

    # --- artifact helpers ---
    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts[artifact.name] = artifact

    def add_context_file(self, artifact: Artifact) -> None:
        """Register an existing repo file as read-only prompting context."""
        self.context_files[artifact.name] = artifact

    @property
    def has_context(self) -> bool:
        return bool(self.context_files)

    def text(self, name: str, default: str = "") -> str:
        art = self.artifacts.get(name)
        return art.content if art else default

    def code_artifacts(self) -> List[Artifact]:
        """Code/test/config files for prompting: existing repo files overlaid by
        anything the pipeline has since produced (same path = an edit)."""
        merged: "dict[str, Artifact]" = dict(self.context_files)
        merged.update(self.artifacts)
        return [a for a in merged.values() if a.type in {"code", "test", "config"}]

    def code_block(self, limit: int = 3500) -> str:
        """Render all code/test/config artifacts as a single prompt-friendly block."""
        parts = []
        for a in self.code_artifacts():
            parts.append(f"--- FILE: {a.name} ({a.language}) ---\n{clip(a.content, limit)}")
        return "\n\n".join(parts) if parts else "(no code yet)"

