"""Base Agent: prompt → LLM → parsed AgentResult."""
from __future__ import annotations

import json
import logging
import re

from ..config import settings
from ..llm.base import LLMProvider
from ..models import AgentResult, Artifact, WorkPackage

logger = logging.getLogger("sdlc.agents")


# --------------------------------------------------------------------------- #
# Truncation-resilient JSON parsing
# --------------------------------------------------------------------------- #
def _scan_string(raw: str, i: int) -> int:
    """Given ``raw[i] == '"'``, return the index just past the closing quote.

    Respects backslash escapes. Returns ``len(raw)`` if the string is
    unterminated (i.e. the response was truncated mid-string).
    """
    n = len(raw)
    i += 1
    while i < n:
        c = raw[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return i + 1
        i += 1
    return n


def _match_object(raw: str, i: int) -> int | None:
    """Given ``raw[i] == '{'``, return the index just past the matching ``}``
    (skipping braces inside strings), or ``None`` if it's truncated."""
    n = len(raw)
    depth = 0
    j = i
    while j < n:
        c = raw[j]
        if c == '"':
            j = _scan_string(raw, j)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return None


def _complete_objects(raw: str, start: int) -> list[str]:
    """From ``start`` (just after an opening ``[``), return each complete,
    brace-balanced ``{...}`` substring, stopping at the first truncated one."""
    objs: list[str] = []
    n = len(raw)
    i = start
    while i < n:
        c = raw[i]
        if c == "]":
            break
        if c != "{":
            i += 1
            continue
        end = _match_object(raw, i)
        if end is None:
            break  # truncated trailing object — drop it
        objs.append(raw[i:end])
        i = end
    return objs


def _recover_artifacts(raw: str) -> list[dict]:
    m = re.search(r'"artifacts"\s*:\s*\[', raw)
    if not m:
        return []
    out: list[dict] = []
    for chunk in _complete_objects(raw, m.end()):
        try:
            out.append(json.loads(chunk))
        except Exception:
            continue
    return out


def _recover_string(raw: str, field: str) -> str:
    m = re.search(rf'"{re.escape(field)}"\s*:\s*"', raw)
    if not m:
        return ""
    start = m.end() - 1  # at the opening quote
    chunk = raw[start:_scan_string(raw, start)]
    try:
        return json.loads(chunk)  # properly unescapes a complete string
    except Exception:
        try:
            return json.loads(chunk + '"')  # close a truncated string
        except Exception:
            return chunk[1:]


def _salvage_truncated(raw: str) -> dict | None:
    """Recover as much as possible from a truncated/garbled JSON response.

    Returns a dict with whatever scalar fields + complete artifacts could be
    parsed, or ``None`` if nothing useful was found. This is what prevents a
    multi-file Developer response from silently producing **zero files** when
    the model output is cut off at the token limit.
    """
    artifacts = _recover_artifacts(raw)
    summary = _recover_string(raw, "summary")
    details = _recover_string(raw, "details")
    verdict = _recover_string(raw, "verdict") or None
    if not (artifacts or summary or details):
        return None
    return {
        "summary": summary,
        "details": details,
        "artifacts": artifacts,
        "verdict": verdict,
        "comments": [],
        "_recovered": True,
    }


def parse_json(raw: str) -> dict:
    """Best-effort JSON extraction from a model response.

    Order of attempts: direct parse → outermost ``{...}`` → salvage complete
    artifacts/fields from a truncated response → raw-as-details fallback.
    """
    raw = (raw or "").strip()
    # Strip Markdown code fences if the model wrapped the JSON.
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw).strip()

    try:
        return json.loads(raw)
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    salvaged = _salvage_truncated(raw)
    if salvaged is not None:
        return salvaged

    return {"summary": raw[:160], "details": raw, "artifacts": []}


class Agent:
    """A role-specialized agent. Subclasses set metadata and ``user_prompt``."""

    id: str = "agent"
    name: str = "Agent"
    emoji: str = "🤖"
    role: str = ""
    system_prompt: str = ""
    # Code-emitting agents (developer/tester) return multiple files in one JSON
    # response, which can be large. They use the bigger ``code_max_tokens`` budget
    # so the response isn't truncated (which would corrupt the JSON → lost files).
    emits_code: bool = False

    def user_prompt(self, wp: WorkPackage) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    async def run(self, wp: WorkPackage, llm: LLMProvider) -> AgentResult:
        max_tokens = settings.code_max_tokens if self.emits_code else settings.max_tokens
        raw = await llm.complete(
            self.system_prompt,
            self.user_prompt(wp),
            tag=self.id,
            json_mode=True,
            max_tokens=max_tokens,
        )
        data = parse_json(raw)

        artifacts = []
        for a in data.get("artifacts", []) or []:
            try:
                artifacts.append(Artifact(**a))
            except Exception:
                # Skip malformed artifact entries rather than failing the run.
                continue

        note = None
        if data.get("_recovered"):
            note = (
                f"Response was truncated; recovered {len(artifacts)} complete file(s). "
                "Raise LLM_CODE_MAX_TOKENS if output looks cut off."
            )
            logger.warning("%s: %s", self.id, note)

        return AgentResult(
            agent_id=self.id,
            agent_name=self.name,
            emoji=self.emoji,
            summary=data.get("summary", ""),
            details=data.get("details", ""),
            artifacts=artifacts,
            verdict=data.get("verdict"),
            comments=list(data.get("comments", []) or []),
            note=note,
        )

