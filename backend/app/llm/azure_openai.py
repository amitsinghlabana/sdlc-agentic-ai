"""Azure OpenAI provider (used when LLM_PROVIDER=azure)."""
from __future__ import annotations

from ..config import Settings
from ..net import build_ssl_verify
from .base import LLMProvider


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
        # Custom HTTP client so TLS verification uses the OS trust store (handles
        # corporate HTTPS inspection); honors LLM_CA_BUNDLE / LLM_VERIFY_SSL.
        http_client = httpx.AsyncClient(
            verify=build_ssl_verify(settings.llm_ca_bundle, settings.llm_verify_ssl),
            timeout=settings.request_timeout,
        )
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
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
        resp = await self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

