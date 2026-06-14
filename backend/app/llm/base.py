"""Abstract LLM provider contract.

Every provider exposes a single async ``complete`` method that takes a system
prompt + user prompt and returns the raw text response. ``json_mode`` requests
a strict JSON object (used by all agents).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str = "base"
    # Human-readable label shown in the UI badge.
    label: str = "Base"

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        *,
        tag: str = "",
        json_mode: bool = True,
        max_tokens: int | None = None,
    ) -> str:
        """Return the model's text response.

        Args:
            system: system / persona prompt.
            user: user message (task + context).
            tag: agent id — used only by the mock provider to pick a template.
            json_mode: request a strict JSON object response.
            max_tokens: optional override of the configured token cap.
        """
        raise NotImplementedError

