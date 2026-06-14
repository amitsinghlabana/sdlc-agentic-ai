"""Admin endpoints: switch providers between mock and live at runtime.

Lets you flip any integration (LLM / JIRA / Foundry IQ / GitHub) between the
free ``mock`` and the real provider WITHOUT editing code, committing, or even
restarting — the choice is persisted (runtime_config) and the affected client
singleton is rebuilt on the spot.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import runtime_config as rc
from ..config import settings
from ..integrations.github import get_github
from ..integrations.jira import get_jira
from ..integrations.knowledge import get_knowledge
from ..llm.factory import get_llm

logger = logging.getLogger("sdlc.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _state() -> dict:
    """Current provider selection + the *effective* client (truth after fallback).

    ``selected`` is what was requested; ``effective`` is what actually loaded —
    they differ when a live provider is chosen but its credentials are missing
    (the factory safely falls back to mock).
    """
    return {
        "providers": {
            "llm": {
                "selected": settings.llm_provider,
                "effective": get_llm().name,
                "options": sorted(rc.ALLOWED["llm_provider"]),
                "configured": {
                    "azure": settings.azure_configured,
                    "openai": settings.openai_configured,
                },
            },
            "knowledge": {
                "selected": settings.knowledge_provider,
                "effective": get_knowledge().name,
                "options": sorted(rc.ALLOWED["knowledge_provider"]),
                "configured": settings.knowledge_configured,
            },
            "jira": {
                "selected": settings.jira_provider,
                "effective": get_jira().name,
                "options": sorted(rc.ALLOWED["jira_provider"]),
                "configured": settings.jira_configured,
            },
            "github": {
                "selected": settings.github_provider,
                "effective": get_github().name,
                "options": sorted(rc.ALLOWED["github_provider"]),
                "configured": settings.github_configured,
            },
        },
        "overrides": rc.load(),
        "persisted_to": str(rc.CONFIG_PATH.name),
    }


@router.get("/providers")
async def get_providers() -> dict:
    return _state()


class ProviderUpdate(BaseModel):
    llm_provider: Optional[str] = None
    jira_provider: Optional[str] = None
    knowledge_provider: Optional[str] = None
    github_provider: Optional[str] = None


@router.post("/providers")
async def set_providers(body: ProviderUpdate) -> dict:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No provider changes supplied.")
    try:
        rc.set_overrides(settings, updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _state()


@router.post("/providers/reset")
async def reset_providers() -> dict:
    """Clear overrides → revert every provider to its ``.env`` value."""
    rc.clear_overrides(settings)
    return _state()

