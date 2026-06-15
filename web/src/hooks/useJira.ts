import { useCallback, useEffect, useState } from "react";
import { toast } from "../store/toast";
import { confirm } from "../store/confirm";
import type { JiraCreatedResult, StoryBundle } from "../lib/types";

export interface JiraStatus {
  provider: string;
  label: string;
  is_mock: boolean;
  configured: boolean;
  host: string;
  project_key: string;
  default_assignee?: string | null;
}

/**
 * JIRA connection info + the outbound create-stories action.
 *
 * `status` tailors the Composer's "Import from JIRA" hint. `createStories()`
 * pushes the generated `stories.json` bundle back to JIRA (optionally under a
 * new epic) via POST /api/jira/create-stories — the human-in-the-loop action
 * that mirrors the original UI.
 */
export function useJira() {
  const [status, setStatus] = useState<JiraStatus | null>(null);
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<JiraCreatedResult | null>(null);

  const refresh = useCallback(() => {
    fetch("/api/jira/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const reset = useCallback(() => setCreated(null), []);

  const createStories = useCallback(
    async (bundle: StoryBundle | null) => {
      if (creating || !bundle || (bundle.stories ?? []).length === 0) return;
      // Confirm before writing to a REAL board.
      if (status && !status.is_mock) {
        const ok = await confirm({
          title: "Create JIRA stories",
          message: `Create ${bundle.stories.length} stories in JIRA (${status.host} / ${status.project_key})?`,
          confirmLabel: "Create",
        });
        if (!ok) return;
      }
      setCreating(true);
      try {
        const r = await fetch("/api/jira/create-stories", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            stories: bundle.stories,
            epic: bundle.epic ?? null,
            create_epic: !!bundle.epic,
          }),
        });
        if (!r.ok) {
          const detail = (await r.json().catch(() => ({})))?.detail;
          throw new Error(detail || `HTTP ${r.status}`);
        }
        const data = (await r.json()) as JiraCreatedResult;
        setCreated(data);
        toast.success(`Created ${data.count} issue(s) in JIRA`);
      } catch (e) {
        toast.error("JIRA create failed: " + (e as Error).message);
      } finally {
        setCreating(false);
      }
    },
    [creating, status],
  );

  return { status, creating, created, createStories, reset, refresh };
}

