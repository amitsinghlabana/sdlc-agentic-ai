"""Vanilla OpenAI provider (used when LLM_PROVIDER=openai)."""
from __future__ import annotations

import logging
import time

from ..config import Settings
from ..net import build_ssl_verify
from .base import LLMProvider

logger = logging.getLogger("sdlc.llm")


class OpenAIProvider(LLMProvider):
    name = "openai"
    label = "OpenAI"

    def __init__(self, settings: Settings) -> None:
        import httpx
        from openai import AsyncOpenAI

        self._settings = settings
        self._model = settings.openai_model
        self.label = f"OpenAI · {self._model}"
        # Short connect phase so a blocked/proxied network fails fast; longer read
        # budget for generation.
        timeout = httpx.Timeout(settings.request_timeout, connect=settings.llm_connect_timeout)
        limits = httpx.Limits() if settings.llm_http_keepalive else httpx.Limits(max_keepalive_connections=0)
        http_client = httpx.AsyncClient(
            verify=build_ssl_verify(settings.llm_ca_bundle, settings.llm_verify_ssl),
            timeout=timeout,
            limits=limits,
        )
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=timeout,
            max_retries=settings.llm_max_retries,
            http_client=http_client,
        )
        logger.info(
            "OpenAI ready: model=%s (connect=%ss read=%ss retries=%s)",
            self._model, settings.llm_connect_timeout, settings.request_timeout,
            settings.llm_max_retries,
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
        logger.info("OpenAI call -> tag=%s model=%s max_tokens=%s (streaming)",
                    tag or "?", self._model, kwargs["max_tokens"])
        t0 = time.perf_counter()
        try:
            # Stream so the read timeout is a per-chunk inactivity window, not a
            # hard cap on the whole response (see AzureOpenAIProvider for details).
            stream = await self._client.chat.completions.create(**kwargs, stream=True)
            parts: list[str] = []
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    parts.append(delta.content)
            content = "".join(parts)
        except Exception as exc:
            dt = time.perf_counter() - t0
            logger.error("OpenAI call FAILED tag=%s after %.1fs: %s: %s",
                         tag or "?", dt, type(exc).__name__, exc)
            raise
        dt = time.perf_counter() - t0
        logger.info("OpenAI call OK tag=%s in %.1fs (%d chars)", tag or "?", dt, len(content))
        return content

