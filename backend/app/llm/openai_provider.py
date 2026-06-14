"""Vanilla OpenAI provider (used when LLM_PROVIDER=openai)."""
from __future__ import annotations

from ..config import Settings
from ..net import build_ssl_verify
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"
    label = "OpenAI"

    def __init__(self, settings: Settings) -> None:
        import httpx
        from openai import AsyncOpenAI

        self._settings = settings
        self._model = settings.openai_model
        self.label = f"OpenAI · {self._model}"
        http_client = httpx.AsyncClient(
            verify=build_ssl_verify(settings.llm_ca_bundle, settings.llm_verify_ssl),
            timeout=settings.request_timeout,
        )
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.request_timeout,
            http_client=http_client,
        )

    async def complete(
        self,
        system: str,
        user: str,
        *,
        tag: str = "",
        json_mode: bool = True,
        max_tokens: int | None = None,
    ) -> str:
        kwargs = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self._settings.temperature,
            "max_tokens": max_tokens or self._settings.max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = await self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

