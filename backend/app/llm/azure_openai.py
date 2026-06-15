"""Azure OpenAI provider (used when LLM_PROVIDER=azure)."""
from __future__ import annotations

import logging
import time

from ..config import Settings
from ..net import build_ssl_verify
from .base import LLMProvider

logger = logging.getLogger("sdlc.llm")


class AzureOpenAIProvider(LLMProvider):
    name = "azure"
    label = "Azure OpenAI"

    def __init__(self, settings: Settings) -> None:
        # Imported lazily so the package works in mock mode without the dependency installed.
        import httpx
        from openai import AsyncAzureOpenAI

        self._settings = settings
        self._deployment = settings.azure_openai_deployment
        self.label = f"Azure OpenAI · {self._deployment}"
        # Granular timeout: a short connect phase so a blocked/proxied network fails
        # fast (instead of hanging the whole read timeout), with the longer read
        # budget for generation. Custom verify uses the OS trust store (handles
        # corporate HTTPS inspection); honors LLM_CA_BUNDLE / LLM_VERIFY_SSL.
        timeout = httpx.Timeout(settings.request_timeout, connect=settings.llm_connect_timeout)
        # Default to NO keep-alive: a corporate proxy can silently drop an idle
        # pooled connection, so reusing it hangs the next call until timeout.
        limits = httpx.Limits() if settings.llm_http_keepalive else httpx.Limits(max_keepalive_connections=0)
        http_client = httpx.AsyncClient(
            verify=build_ssl_verify(settings.llm_ca_bundle, settings.llm_verify_ssl),
            timeout=timeout,
            limits=limits,
        )
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            timeout=timeout,
            max_retries=settings.llm_max_retries,
            http_client=http_client,
        )
        logger.info(
            "Azure OpenAI ready: endpoint=%s deployment=%s api_version=%s "
            "(connect=%ss read=%ss retries=%s)",
            settings.azure_openai_endpoint, self._deployment, settings.azure_openai_api_version,
            settings.llm_connect_timeout, settings.request_timeout, settings.llm_max_retries,
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
            "model": self._deployment,  # Azure uses the *deployment* name here
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self._settings.temperature,
            "max_tokens": max_tokens or self._settings.max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        logger.info("Azure call → tag=%s deployment=%s max_tokens=%s",
                    tag or "?", self._deployment, kwargs["max_tokens"])
        t0 = time.perf_counter()
        try:
            resp = await self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            dt = time.perf_counter() - t0
            logger.error("Azure call ✗ tag=%s after %.1fs: %s: %s",
                         tag or "?", dt, type(exc).__name__, exc)
            raise
        dt = time.perf_counter() - t0
        content = resp.choices[0].message.content or ""
        logger.info("Azure call ✓ tag=%s in %.1fs (%d chars)", tag or "?", dt, len(content))
        return content

