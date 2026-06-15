"""Orchestrator — runs the agent pipeline and streams events.

Pattern: Orchestrator-Worker + Sequential Pipeline with a Reviewer→Developer
feedback loop (capped by ``settings.max_review_loops``).

``run_pipeline`` is an async generator that yields plain dict events. The API
layer turns these into Server-Sent Events; tests consume them directly.

Event types:
  run_start    {request, provider, provider_label}
  plan         {steps: [{id,name,emoji,role}]}
  grounding    {provider, label, citations:[...], subqueries:[...], count}
  agent_start  {agent, name, emoji, role, iteration}
  delta        {agent, text}            # streamed text for the typing effect
  artifact     {agent, artifact}        # one produced file
  agent_done  {agent, summary, verdict, comments}
  loop         {iteration, comments, final}  # reviewer requested changes; final=cap reached
  run_complete {artifacts: [...summary], duration_ms}
  error        {agent?, message}
"""
from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator, Dict, List, Optional

from .agents import build_team
from .config import settings
from .integrations.knowledge import get_knowledge
from .llm.base import LLMProvider
from .models import AgentResult, Artifact, WorkPackage, infer_artifact


def _event(type_: str, **data) -> dict:
    return {"type": type_, **data}


def _chunks(text: str, words_per_chunk: int = 5):
    """Yield small word groups so the UI can render a live typing effect."""
    if not text:
        return
    words = text.split(" ")
    for i in range(0, len(words), words_per_chunk):
        piece = " ".join(words[i : i + words_per_chunk])
        # Preserve a trailing space between chunks (except the last).
        yield piece + (" " if i + words_per_chunk < len(words) else "")


async def _emit_result(agent, result: AgentResult, wp: WorkPackage) -> AsyncIterator[dict]:
    """Stream an agent's textual output, then its artifacts and completion."""
    text = result.details or result.summary
    for chunk in _chunks(text):
        yield _event("delta", agent=agent.id, text=chunk)
        if settings.stream_delay:
            await asyncio.sleep(settings.stream_delay)

    for artifact in result.artifacts:
        wp.add_artifact(artifact)
        yield _event("artifact", agent=agent.id, artifact=artifact.model_dump())

    wp.history.append(result)
    yield _event(
        "agent_done",
        agent=agent.id,
        summary=result.summary,
        verdict=result.verdict,
        comments=result.comments,
        note=result.note,
    )


async def _ground(wp: WorkPackage) -> AsyncIterator[dict]:
    """Foundry IQ grounding: retrieve cited company standards before agents run."""
    client = get_knowledge()
    try:
        result = await client.retrieve(wp.request, top=settings.knowledge_top_k)
    except Exception as exc:  # best-effort — never block the pipeline on grounding
        yield _event("grounding", provider=client.name, label=getattr(client, "label", client.name),
                     citations=[], subqueries=[], count=0, error=f"{type(exc).__name__}: {exc}")
        return

    wp.grounding_block = result.as_prompt_block()
    wp.citations = [c.model_dump() for c in result.citations]

    yield _event(
        "grounding",
        provider=result.provider,
        label=getattr(client, "label", result.provider),
        citations=wp.citations,
        subqueries=result.subqueries,
        count=len(result.citations),
    )
    if result.citations:
        artifact = Artifact(
            name="grounding.md", type="doc", language="markdown", content=result.to_markdown()
        )
        wp.add_artifact(artifact)
        yield _event("artifact", agent="knowledge", artifact=artifact.model_dump())


async def _run_agent(agent, wp: WorkPackage, llm: LLMProvider, iteration: int = 0) -> AsyncIterator[dict]:
    yield _event(
        "agent_start",
        agent=agent.id,
        name=agent.name,
        emoji=agent.emoji,
        role=agent.role,
        iteration=iteration,
    )
    try:
        result = await agent.run(wp, llm)
    except Exception as exc:  # surface a clean error event instead of crashing the stream
        yield _event("error", agent=agent.id, message=f"{type(exc).__name__}: {exc}")
        # Record an empty result so the pipeline can continue gracefully.
        result = AgentResult(agent_id=agent.id, agent_name=agent.name, emoji=agent.emoji,
                             summary=f"(failed: {exc})")
        wp.history.append(result)
        yield _event("agent_done", agent=agent.id, summary=result.summary, verdict=None, comments=[])
        return

    async for ev in _emit_result(agent, result, wp):
        yield ev


async def _review_loop(team, wp: WorkPackage, llm: LLMProvider) -> AsyncIterator[dict]:
    """Reviewer→Developer feedback loop, capped by ``settings.max_review_loops``.

    The reviewer inspects the current code; if it requests changes, the Developer
    (and Tester) address them and we re-review — until the reviewer approves or
    the cap is reached. When the cap is hit while changes are STILL requested, the
    Developer applies one FINAL revision (so feedback is never silently dropped)
    and the loop ends without another review pass — instead of stranding the run
    on an unresolved "request_changes". That final loop-back is flagged ``final``.
    """
    loop = 0
    while True:
        async for ev in _run_agent(team["reviewer"], wp, llm, iteration=loop):
            yield ev
        last = wp.history[-1]
        if last.verdict != "request_changes":
            return  # approved (or no blocking verdict) → review complete

        capped = loop >= settings.max_review_loops
        loop += 1
        wp.review_feedback = last.comments
        yield _event("loop", iteration=loop, comments=last.comments, final=capped)
        async for ev in _run_agent(team["developer"], wp, llm, iteration=loop):
            yield ev
        async for ev in _run_agent(team["tester"], wp, llm, iteration=loop):
            yield ev
        if capped:
            return  # final revision applied; stop without another review pass


async def run_pipeline(
    request: str,
    llm: LLMProvider,
    *,
    seed_files: Optional[List] = None,
    repo: Optional[str] = None,
) -> AsyncIterator[dict]:
    """Execute the full SDLC agent pipeline for a single request.

    When ``seed_files`` (existing repo ``RepoFile``s) are supplied, they're loaded
    as read-only context so the Developer **edits the real codebase** and the run
    targets ``repo`` for a branch + PR.
    """
    start = time.perf_counter()
    team: Dict[str, object] = build_team()

    yield _event(
        "run_start",
        request=request,
        provider=llm.name,
        provider_label=getattr(llm, "label", llm.name),
    )
    yield _event(
        "plan",
        steps=[
            {"id": a.id, "name": a.name, "emoji": a.emoji, "role": a.role}
            for a in (team["requirements"], team["architect"], team["developer"],
                      team["tester"], team["reviewer"], team["docs"])
        ],
    )

    wp = WorkPackage(request)

    # 0a) Existing-repo context — seed the codebase the agents will edit.
    if seed_files:
        wp.repo = repo
        for rf in seed_files:
            wp.add_context_file(infer_artifact(rf.path, getattr(rf, "content", "") or ""))
        yield _event(
            "repo_context",
            repo=repo,
            count=len(wp.context_files),
            files=[
                {"path": a.name, "bytes": len((a.content or "").encode("utf-8"))}
                for a in wp.context_files.values()
            ],
        )

    # 0b) Foundry IQ grounding — retrieve cited standards to ground the agents.
    async for ev in _ground(wp):
        yield ev

    # 1) Requirements → 2) Architect (sequential)
    async for ev in _run_agent(team["requirements"], wp, llm):
        yield ev
    async for ev in _run_agent(team["architect"], wp, llm):
        yield ev

    # 3) Developer → 4) Tester → 5) Reviewer, looping on requested changes.
    async for ev in _run_agent(team["developer"], wp, llm):
        yield ev
    async for ev in _run_agent(team["tester"], wp, llm):
        yield ev

    # 5) Reviewer with a capped Reviewer→Developer feedback loop. See
    #    ``_review_loop``: the Developer always addresses the reviewer's comments
    #    (including a final revision when the cap is reached), so the run never
    #    strands on an unresolved "request_changes".
    async for ev in _review_loop(team, wp, llm):
        yield ev

    # 6) Documentation
    async for ev in _run_agent(team["docs"], wp, llm):
        yield ev

    duration_ms = int((time.perf_counter() - start) * 1000)
    yield _event(
        "run_complete",
        duration_ms=duration_ms,
        artifacts=[
            {"name": a.name, "type": a.type, "language": a.language}
            for a in wp.artifacts.values()
        ],
    )

