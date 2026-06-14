import { useCallback, useEffect, useState } from "react";
import { toast } from "../store/toast";
import type { Artifact, PublishOptions, PublishResult } from "../lib/types";

interface GitHubStatus {
  provider: string;
  is_mock: boolean;
  repo: string;
  repo_url: string;
  owner?: string;
  has_default_repo?: boolean;
}

/**
 * GitHub info + the outbound publish action for the UI.
 *
 * `status`/`repos` power the header badge and the "edit existing repo" picker;
 * `publish()` pushes the SELECTED generated artifacts to GitHub — opening a
 * branch + PR against an existing repo, or creating a brand-new repo — via
 * POST /api/github/publish (human-in-the-loop, mirrors the original UI).
 */
export function useGitHub() {
  const [status, setStatus] = useState<GitHubStatus | null>(null);
  const [repos, setRepos] = useState<string[]>([]);
  const [publishing, setPublishing] = useState(false);
  const [result, setResult] = useState<PublishResult | null>(null);

  const refresh = useCallback(() => {
    fetch("/api/github/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus(null));
    fetch("/api/github/repos")
      .then((r) => r.json())
      .then((d) => setRepos(d.repos ?? []))
      .catch(() => setRepos([]));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const reset = useCallback(() => setResult(null), []);

  const publish = useCallback(
    async (files: Artifact[], title: string, opts: PublishOptions = {}) => {
      const list: Artifact[] = Array.isArray(files) ? files : Object.values(files ?? {});
      if (publishing || list.length === 0) return;
      const repo = (opts.repo ?? "").trim();
      const createNew = !!opts.createNew;

      // Confirm before writing to a REAL repo.
      if (status && !status.is_mock) {
        let action: string;
        if (createNew) {
          action = repo.includes("/")
            ? `create new repo ${repo} and push`
            : `create a new repo under ${status.owner || "your account"} and push`;
        } else {
          action = `open a PR against ${repo}`;
        }
        if (!globalThis.confirm(`Publish ${list.length} file(s) to GitHub — ${action}?`)) return;
      }

      setPublishing(true);
      try {
        const r = await fetch("/api/github/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: (title || "SDLC feature").slice(0, 120),
            request: title || "", // original feature → better AI commit msg
            repo: repo || null, // empty + owner-only → backend auto-names a new repo
            create_new: createNew,
            branch: opts.branch?.trim() || null,
            artifacts: list.map((a) => ({ name: a.name, content: a.content })),
          }),
        });
        if (!r.ok) {
          const detail = (await r.json().catch(() => ({})))?.detail;
          throw new Error(detail || `HTTP ${r.status}`);
        }
        const data = (await r.json()) as PublishResult;
        setResult(data);
        toast.success(
          data.mode === "new_repo"
            ? `Created ${data.repo} & pushed`
            : `Opened PR #${data.pull_request?.number}`,
        );
      } catch (e) {
        toast.error("GitHub publish failed: " + (e as Error).message);
      } finally {
        setPublishing(false);
      }
    },
    [publishing, status],
  );

  return { status, repos, publishing, result, publish, reset, refresh };
}

