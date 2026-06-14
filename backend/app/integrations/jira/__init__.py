"""JIRA integration package.

Mirrors the ``llm/`` provider pattern: an abstract ``JiraClient`` with a free
offline ``MockJiraClient`` (default) and a future real ``CloudJiraClient``,
selected by a ``get_jira()`` factory keyed on ``JIRA_PROVIDER``.
"""
from .factory import get_jira, reset_jira  # noqa: F401

