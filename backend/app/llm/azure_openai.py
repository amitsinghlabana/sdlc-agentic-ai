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
        # Per-model API quirks, discovered on first call and then cached so we only
        # pay the failed attempt once. Lets you swap the deployment in the Render
        # dashboard to ANY model family (incl. codex / reasoning models) without a
        # code change: such models reject `temperature`/`max_tokens` and may not
        # stream, so we adapt automatically on the first 400 and remember it.
        self._use_max_completion_tokens = False
        self._drop_temperature = False
        self._no_stream = False
        # Some models (codex / gpt-5 reasoning) are served ONLY by the Responses
        # API, not Chat Completions. When the deployment rejects Chat Completions
        # we flip this and route to a lazily-built Responses client (which needs a
        # newer api-version). Cached so we only probe once.
        self._use_responses_api = False
        self._responses_client = None
        self._drop_reasoning = False
        # Granular timeout: a short connect phase so a blocked/proxied network fails
        # fast (instead of hanging the whole read timeout), with the longer read
        # budget for generation. Custom verify uses the OS trust store (handles
        # corporate HTTPS inspection); honors LLM_CA_BUNDLE / LLM_VERIFY_SSL.
        timeout = httpx.Timeout(settings.request_timeout, connect=settings.llm_connect_timeout)
        # Default to NO keep-alive: a corporate proxy can silently drop an idle
        # pooled connection, so reusing it hangs the next call until timeout.
        limits = httpx.Limits() if settings.llm_http_keepalive else httpx.Limits(max_keepalive_connections=0)
        self._verify = build_ssl_verify(settings.llm_ca_bundle, settings.llm_verify_ssl)
        self._timeout = timeout
        self._limits = limits
        http_client = httpx.AsyncClient(
            verify=self._verify,
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

    def _build_kwargs(self, system: str, user: str, json_mode: bool, token_budget: int) -> dict:
        kwargs: dict = {
            "model": self._deployment,  # Azure uses the *deployment* name here
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        # Newer reasoning/codex models renamed this parameter.
        if self._use_max_completion_tokens:
            kwargs["max_completion_tokens"] = token_budget
        else:
            kwargs["max_tokens"] = token_budget
        # Some reasoning/codex models only accept the default temperature.
        if not self._drop_temperature:
            kwargs["temperature"] = self._settings.temperature
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    def _adapt(self, exc: Exception) -> bool:
        """If the error is a known unsupported-parameter 400, flip a flag and
        signal a retry. Returns True if we adapted (caller should retry)."""
        msg = str(exc).lower()
        if "400" not in msg and "bad request" not in msg and "unsupported" not in msg \
                and "does not support" not in msg and "not supported" not in msg:
            return False
        # Whole-operation unsupported → this deployment isn't served by Chat
        # Completions at all (codex / gpt-5 reasoning). Switch to the Responses API.
        if ("operation is unsupported" in msg or "unsupported operation" in msg) \
                and not self._use_responses_api:
            self._use_responses_api = True
            logger.warning("Azure: deployment not served by Chat Completions — "
                           "switching to the Responses API and retrying.")
            return True
        if "max_completion_tokens" in msg and not self._use_max_completion_tokens:
            self._use_max_completion_tokens = True
            logger.warning("Azure: model needs max_completion_tokens — adapting and retrying.")
            return True
        if "temperature" in msg and not self._drop_temperature:
            self._drop_temperature = True
            logger.warning("Azure: model rejects custom temperature — dropping it and retrying.")
            return True
        if "stream" in msg and not self._no_stream:
            self._no_stream = True
            logger.warning("Azure: model can't stream — falling back to a single call and retrying.")
            return True
        return False

    def _responses(self):
        """Lazily build a client for the Responses API (needs a newer api-version
        than Chat Completions, so it can't be the same client)."""
        if self._responses_client is None:
            import httpx
            from openai import AsyncAzureOpenAI

            self._responses_client = AsyncAzureOpenAI(
                api_key=self._settings.azure_openai_api_key,
                api_version=self._settings.azure_responses_api_version,
                azure_endpoint=self._settings.azure_openai_endpoint,
                timeout=self._timeout,
                max_retries=self._settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    verify=self._verify, timeout=self._timeout, limits=self._limits
                ),
            )
        return self._responses_client

    async def _run_responses(self, system: str, user: str, json_mode: bool, token_budget: int) -> str:
        # Responses API: system → `instructions`, user → `input`. Reasoning models
        # spend tokens on hidden reasoning, so give a floor or `output_text` can be
        # empty. JSON mode requires the literal word "json" in the input.
        if json_mode and "json" not in user.lower():
            user = user + "\n\nRespond ONLY with a valid JSON object."
        kwargs: dict = {
            "model": self._deployment,
            "instructions": system,
            "input": user,
            "max_output_tokens": max(token_budget, 4000),
        }
        # Reasoning models accept an effort hint; "low" keeps structured generation
        # fast + reliable. Harmless if the model ignores it.
        effort = getattr(self._settings, "azure_reasoning_effort", "") or ""
        if effort and not self._drop_reasoning:
            kwargs["reasoning"] = {"effort": effort}
        if json_mode:
            kwargs["text"] = {"format": {"type": "json_object"}}
        client = self._responses()
        if self._no_stream:
            resp = await client.responses.create(**kwargs)
            return resp.output_text or ""
        stream = await client.responses.create(**kwargs, stream=True)
        parts: list[str] = []
        async for ev in stream:
            if getattr(ev, "type", "") == "response.output_text.delta":
                parts.append(getattr(ev, "delta", "") or "")
        return "".join(parts)

    async def _run(self, system: str, user: str, json_mode: bool, token_budget: int) -> str:
        if self._use_responses_api:
            return await self._run_responses(system, user, json_mode, token_budget)
        kwargs = self._build_kwargs(system, user, json_mode, token_budget)
        if self._no_stream:
            resp = await self._client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        # Stream so the httpx read timeout acts as a per-chunk INACTIVITY window
        # rather than a hard cap on the whole answer — a long but steady generation
        # then can't trip the timeout mid-response (what made the pipeline look stuck).
        stream = await self._client.chat.completions.create(**kwargs, stream=True)
        parts: list[str] = []
        async for chunk in stream:
            if not chunk.choices:
                continue  # usage / content-filter frames carry no choices
            delta = chunk.choices[0].delta
            if delta and delta.content:
                parts.append(delta.content)
        return "".join(parts)

    async def complete(
        self,
        system: str,
        user: str,
        *,
        tag: str = "",
        json_mode: bool = True,
        max_tokens: int | None = None,
    ) -> str:
        token_budget = max_tokens or self._settings.max_tokens
        logger.info("Azure call -> tag=%s deployment=%s max_tokens=%s (streaming=%s)",
                    tag or "?", self._deployment, token_budget, not self._no_stream)
        t0 = time.perf_counter()
        # Up to 5 one-time adaptations (responses-API / token param / temperature /
        # streaming / reasoning), each flag cached, + a final attempt that surfaces
        # real errors.
        for _ in range(6):
            try:
                content = await self._run(system, user, json_mode, token_budget)
            except Exception as exc:
                if self._adapt(exc):
                    continue  # known quirk → flag flipped, retry
                dt = time.perf_counter() - t0
                logger.error("Azure call FAILED tag=%s after %.1fs: %s: %s",
                             tag or "?", dt, type(exc).__name__, exc)
                raise
            dt = time.perf_counter() - t0
            api = "responses" if self._use_responses_api else "chat"
            logger.info("Azure call OK tag=%s via %s in %.1fs (%d chars)",
                        tag or "?", api, dt, len(content))
            return content
        # Exhausted adaptations — make a final attempt so the real error surfaces.
        return await self._run(system, user, json_mode, token_budget)

