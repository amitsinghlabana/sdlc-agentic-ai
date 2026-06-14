"""Knowledge / agentic-retrieval integration package (**Microsoft Foundry IQ**).

Mirrors the ``llm/`` and ``jira/`` provider patterns: an abstract
``KnowledgeClient`` with a free offline ``MockKnowledgeClient`` (default) and a
real ``FoundryKnowledgeClient`` (Azure AI Foundry / AI Search agentic
retrieval), selected by ``get_knowledge()`` keyed on ``KNOWLEDGE_PROVIDER``.

Grounding agents in cited, retrieved company standards is how this project
satisfies the "integrate a Microsoft IQ intelligence layer" requirement.
"""
from .factory import get_knowledge, reset_knowledge  # noqa: F401

