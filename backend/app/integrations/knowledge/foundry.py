"""Real **Foundry IQ** knowledge client (used when ``KNOWLEDGE_PROVIDER=foundry``).

Calls Azure AI Foundry / Azure AI Search **agentic retrieval** ("knowledge
agent") over HTTPS and maps the response into provider-agnostic
``RetrievalResult`` citations. Mirrors the lazy/defensive style of
``jira/cloud.py`` and reuses the shared OS-trust-store TLS helper (``net.py``)
so it survives corporate HTTPS inspection.

The exact agentic-retrieval schema is still evolving, so parsing is deliberately
tolerant and everything is config-driven (endpoint, agent, index, api-version).
Retrieval is best-effort: on any error it logs and returns an empty result so a
live demo never crashes — the pipeline simply runs ungrounded.
"""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

import httpx

from ...net import build_ssl_verify
from .base import KnowledgeClient
from .models import Citation, RetrievalResult

logger = logging.getLogger("sdlc.knowledge")


def _first_text(content: Any) -> str:
    """Pull text out of an OpenAI-style content array or a plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") in (None, "text") and part.get("text"):
                return str(part["text"])
    return ""


class FoundryKnowledgeClient(KnowledgeClient):
    name = "foundry"
    label = "Foundry IQ"

    def __init__(self, settings: Any, *, transport: Optional[httpx.BaseTransport] = None) -> None:
        self._endpoint = (settings.foundry_search_endpoint or "").rstrip("/")
        self._agent = settings.foundry_knowledge_agent
        self._index = settings.foundry_index
        self._api_version = settings.foundry_api_version
        self._key = settings.foundry_api_key
        self._transport = transport  # injected by tests (httpx.MockTransport)
        self._verify = build_ssl_verify(
            getattr(settings, "knowledge_ca_bundle", "") or "",
            getattr(settings, "knowledge_verify_ssl", True),
        )
        self._timeout = httpx.Timeout(float(getattr(settings, "request_timeout", 60.0)))
        host = self._endpoint.split("//")[-1]
        self.label = f"Foundry IQ · {host}" if host else "Foundry IQ"

    # ------------------------------------------------------------------ #
    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self._timeout,
            transport=self._transport,
            verify=self._verify,
            headers={
                "api-key": self._key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def _url(self) -> str:
        return f"{self._endpoint}/agents/{self._agent}/retrieve?api-version={self._api_version}"

    def _build_body(self, query: str) -> dict:
        body: dict = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": query}]}],
        }
        if self._index:
            # Azure requires maxDocsForReranker in (100, 2000]; the number of
            # citations actually returned is capped by ``top`` in ``_parse``.
            body["targetIndexParams"] = [{"indexName": self._index, "maxDocsForReranker": 200}]
        return body

    # ------------------------------------------------------------------ #
    def _parse_references(self, references: list, top: int) -> List[Citation]:
        citations: List[Citation] = []
        for i, ref in enumerate(references[:top], start=1):
            src_data = ref.get("sourceData") or ref.get("source") or {}
            if not isinstance(src_data, dict):
                src_data = {}
            title = src_data.get("title") or src_data.get("name") or ref.get("docKey") or f"Reference {i}"
            snippet = (
                src_data.get("content")
                or src_data.get("chunk")
                or src_data.get("text")
                or src_data.get("terms")
                or ""
            )
            citations.append(
                Citation(
                    id=f"S{i}",
                    title=str(title)[:120],
                    source=str(src_data.get("source") or self._index or "foundry"),
                    url=str(src_data.get("url") or ""),
                    snippet=" ".join(str(snippet).split())[:240],
                    score=float(ref.get("rerankerScore") or ref.get("score") or 0.0),
                )
            )
        return citations

    @staticmethod
    def _parse_fallback(data: dict) -> List[Citation]:
        """Use the synthesized grounded answer when there are no references."""
        for item in data.get("response") or []:
            text = _first_text(item.get("content"))
            if text:
                return [Citation(id="S1", title="Grounded answer", source="foundry",
                                 snippet=" ".join(text.split())[:240])]
        return []

    @staticmethod
    def _parse_subqueries(data: dict) -> List[str]:
        subqueries: List[str] = []
        for act in data.get("activity") or []:
            q = act.get("query")
            if isinstance(q, dict) and q.get("search"):
                subqueries.append(str(q["search"]))
            elif isinstance(q, str):
                subqueries.append(q)
        return subqueries

    @staticmethod
    def _parse_response_json(data: dict, top: int) -> List[Citation]:
        """Primary shape: response[0].content[0].text is a JSON array of
        {ref_id, title, terms, content} — the grounded, citable chunks."""
        for item in data.get("response") or []:
            text = _first_text(item.get("content"))
            if not text:
                continue
            try:
                entries = json.loads(text)
            except (ValueError, TypeError):
                continue
            if not isinstance(entries, list):
                continue
            citations: List[Citation] = []
            for i, e in enumerate(entries[:top], start=1):
                if not isinstance(e, dict):
                    continue
                citations.append(
                    Citation(
                        id=f"S{i}",
                        title=str(e.get("title") or f"Reference {i}")[:120],
                        source=str(e.get("terms") or e.get("source") or ""),
                        url=str(e.get("url") or ""),
                        snippet=" ".join(str(e.get("content") or "").split())[:240],
                        score=float(e.get("rerankerScore") or e.get("score") or 0.0),
                    )
                )
            if citations:
                return citations
        return []

    def _parse(self, query: str, data: dict, top: int) -> RetrievalResult:
        citations = self._parse_response_json(data, top)
        if not citations:
            citations = self._parse_references(data.get("references") or [], top)
        if not citations:
            citations = self._parse_fallback(data)
        return RetrievalResult(
            query=query,
            citations=citations,
            subqueries=self._parse_subqueries(data),
            provider=self.name,
        )

    async def retrieve(self, query: str, *, top: int = 5) -> RetrievalResult:
        try:
            async with self._client() as http:
                resp = await http.post(self._url(), json=self._build_body(query))
            if resp.status_code >= 400:
                reason = self._error_reason(resp)
                logger.warning("Foundry IQ retrieve -> %s: %s", resp.status_code, resp.text[:300])
                return RetrievalResult(
                    query=query,
                    provider=self.name,
                    error=f"HTTP {resp.status_code}: {reason}"[:300],
                )
            return self._parse(query, resp.json(), top)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Foundry IQ retrieve failed; running ungrounded.", exc_info=True)
            return RetrievalResult(
                query=query, provider=self.name, error=f"{type(exc).__name__}: {exc}"[:300]
            )

    @staticmethod
    def _error_reason(resp: httpx.Response) -> str:
        """Pull a human-readable reason out of a Foundry/Azure error body."""
        try:
            body = resp.json()
            err = body.get("error")
            if isinstance(err, dict):
                return str(err.get("message") or err.get("code") or resp.text)[:280]
            if isinstance(err, str):
                return err[:280]
        except (ValueError, TypeError):
            pass
        return (resp.text or resp.reason_phrase or "request failed")[:280]



