import { useCallback, useEffect, useState } from "react";
import { toast } from "../store/toast";
import { confirm } from "../store/confirm";
import type { ImportedIssue, JiraCreatedResult, StoryBundle } from "../lib/types";

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
    async (bundle: StoryBundle | null, imported?: ImportedIssue | null) => {
      if (creating || !bundle || (bundle.stories ?? []).length === 0) return;

      const importType = (imported?.type ?? "").toLowerCase();
      const isEpic = importType === "epic";
      const isStory = !!imported && !isEpic;
      const n = bundle.stories.length;
      const subCount = bundle.stories.reduce(
        (a, s) => a + (s.subtasks?.length ? s.subtasks.length : 1),
        0,
      );

      // Build an accurate, context-aware action description.
      let action: string;
      if (isStory) action = `Add ${subCount} sub-task${subCount === 1 ? "" : "s"} under ${imported!.key}`;
      else if (isEpic) action = `Create ${n} stor${n === 1 ? "y" : "ies"} under epic ${imported!.key}`;
      else action = `Create ${n} stor${n === 1 ? "y" : "ies"} in JIRA`;

      // Confirm before writing to a REAL board.
      if (status && !status.is_mock) {
        const ok = await confirm({
          title: "Create in JIRA",
          message: `${action} (${status.host} / ${status.project_key})?`,
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
            // Only create a brand-new epic when nothing was imported.
            create_epic: !imported && !!bundle.epic,
            import_key: imported?.key ?? null,
            import_type: imported?.type ?? null,
          }),
        });
        if (!r.ok) {
          const detail = (await r.json().catch(() => ({})))?.detail;
          throw new Error(detail || `HTTP ${r.status}`);
        }
        const data = (await r.json()) as JiraCreatedResult;
        setCreated(data);
        const noun = data.mode === "subtasks" ? "sub-task" : "issue";
        toast.success(`Created ${data.count} ${noun}${data.count === 1 ? "" : "s"} in JIRA`);
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

