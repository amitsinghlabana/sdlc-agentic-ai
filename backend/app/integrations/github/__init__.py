"""GitHub integration package.

Mirrors the ``jira/`` provider pattern: an abstract ``GitHubClient`` with a free
offline ``MockGitHubClient`` (default) and a real ``CloudGitHubClient`` (GitHub
REST API), selected by ``get_github()`` keyed on ``GITHUB_PROVIDER``.

Outbound: turn the pipeline's artifacts into a branch + Pull Request (existing
repo) or a freshly-created repo (new feature). Inbound: import a GitHub issue as
a feature request.
"""
from .factory import get_github, reset_github  # noqa: F401

