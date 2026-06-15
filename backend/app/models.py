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


# Extension → (type, language) for files read back from an existing repo AND for
# normalizing the artifacts agents generate (so a file's path is the source of
# truth for its language, even if the model mislabels it).
_EXT_MAP: dict[str, tuple[str, str]] = {
    # Python
    ".py": ("code", "python"), ".pyi": ("code", "python"),
    # JS / TS
    ".js": ("code", "javascript"), ".jsx": ("code", "javascript"),
    ".mjs": ("code", "javascript"), ".cjs": ("code", "javascript"),
    ".ts": ("code", "typescript"), ".tsx": ("code", "typescript"),
    ".vue": ("code", "vue"), ".svelte": ("code", "svelte"),
    # Web
    ".html": ("code", "html"), ".htm": ("code", "html"),
    ".css": ("code", "css"), ".scss": ("code", "scss"), ".sass": ("code", "scss"),
    ".less": ("code", "less"), ".xml": ("code", "xml"),
    # JVM
    ".java": ("code", "java"), ".kt": ("code", "kotlin"), ".kts": ("code", "kotlin"),
    ".scala": ("code", "scala"), ".groovy": ("code", "groovy"), ".gradle": ("config", "groovy"),
    # Systems
    ".go": ("code", "go"), ".rs": ("code", "rust"),
    ".c": ("code", "c"), ".h": ("code", "c"),
    ".cpp": ("code", "cpp"), ".cc": ("code", "cpp"), ".cxx": ("code", "cpp"),
    ".hpp": ("code", "cpp"), ".hh": ("code", "cpp"),
    ".cs": ("code", "csharp"), ".swift": ("code", "swift"), ".m": ("code", "objectivec"),
    # Scripting / other
    ".rb": ("code", "ruby"), ".php": ("code", "php"), ".pl": ("code", "perl"),
    ".lua": ("code", "lua"), ".r": ("code", "r"), ".dart": ("code", "dart"),
    ".ex": ("code", "elixir"), ".exs": ("code", "elixir"), ".clj": ("code", "clojure"),
    ".sh": ("code", "bash"), ".bash": ("code", "bash"), ".zsh": ("code", "bash"),
    ".ps1": ("code", "powershell"), ".bat": ("code", "batch"), ".cmd": ("code", "batch"),
    ".sql": ("code", "sql"), ".graphql": ("code", "graphql"), ".gql": ("code", "graphql"),
    ".proto": ("code", "protobuf"),
    # Config / data
    ".json": ("config", "json"), ".jsonc": ("config", "json"),
    ".yaml": ("config", "yaml"), ".yml": ("config", "yaml"),
    ".toml": ("config", "toml"), ".ini": ("config", "ini"), ".cfg": ("config", "ini"),
    ".env": ("config", "bash"), ".tf": ("config", "terraform"), ".hcl": ("config", "terraform"),
    # Docs
    ".md": ("doc", "markdown"), ".markdown": ("doc", "markdown"),
    ".rst": ("doc", "text"), ".txt": ("doc", "text"),
}

# Extensionless / special filenames → (type, language).
_NAME_MAP: dict[str, tuple[str, str]] = {
    "dockerfile": ("config", "dockerfile"),
    "makefile": ("config", "makefile"),
    "procfile": ("config", "yaml"),
    ".gitignore": ("config", "text"), ".dockerignore": ("config", "text"),
    ".env": ("config", "bash"), ".env.example": ("config", "bash"),
    "requirements.txt": ("config", "text"), "go.mod": ("config", "text"), "go.sum": ("config", "text"),
}


def _type_language_for(path: str) -> tuple[Optional[str], Optional[str]]:
    """Return (type, language) for a path from its filename/extension, or
    (None, None) when unknown."""
    base = path.rsplit("/", 1)[-1].lower()
    if base in _NAME_MAP:
        return _NAME_MAP[base]
    ext = "." + base.rsplit(".", 1)[-1] if "." in base else ""
    return _EXT_MAP.get(ext, (None, None))


def _is_test_path(path: str) -> bool:
    p = path.lower()
    base = p.rsplit("/", 1)[-1]
    return (
        base.startswith("test_")
        or base.endswith("_test.py")
        or base.endswith("_test.go")
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
    type_, language = _type_language_for(path)
    type_ = type_ or "code"
    language = language or "text"
    if _is_test_path(path) and type_ == "code":
        type_ = "test"
    return Artifact(name=path, type=type_, language=language, content=content)


def refine_artifact(art: "Artifact") -> "Artifact":
    """Normalize a generated artifact's type/language from its filename.

    Agents sometimes omit or mislabel ``language``/``type``; the file's path is a
    more reliable signal, so we derive them from the extension when it's known.
    Keeps the model's values for unknown extensions, and always honors test paths.
    """
    etype, elang = _type_language_for(art.name)
    if elang:
        art.language = elang
    elif not art.language:
        art.language = "text"
    if etype:
        art.type = etype
    elif not art.type:
        art.type = "code"
    # A file under tests/ (or named *_test/*.spec) is a test, even if tagged code.
    if (art.type in {"code", "test"}) and (_is_test_path(art.name)):
        art.type = "test"
    return art


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

