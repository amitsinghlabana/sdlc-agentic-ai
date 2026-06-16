import { useMemo } from "react";
import type { Artifact, Story, StoryBundle } from "../lib/types";

/** Strip an accidental ```json … ``` code fence the model sometimes adds. */
function stripFence(text: string): string {
  const t = text.trim();
  if (!t.startsWith("```")) return t;
  return t
    .replace(/^```[a-zA-Z]*\s*/, "")
    .replace(/\s*```$/, "")
    .trim();
}

/**
 * Parse the `stories.json` artifact (if the Requirements agent produced one)
 * into a StoryBundle for the JIRA push panel. Accepts either a bare array of
 * stories or an object `{ epic, stories }`. Returns null when absent/invalid.
 *
 * Robust to the file living at a nested path (e.g. `docs/stories.json`): the
 * real LLM uses "proper project layout" paths, so we match by basename rather
 * than an exact `stories.json` key.
 */
export function useStoryBundle(artifacts: Record<string, Artifact>): StoryBundle | null {
  return useMemo(() => {
    // Prefer an exact root match; else any artifact named stories.json in a folder.
    const key =
      "stories.json" in artifacts
        ? "stories.json"
        : Object.keys(artifacts).find(
            (k) => k.toLowerCase().split("/").pop() === "stories.json",
          );
    const art = key ? artifacts[key] : undefined;
    if (!art) return null;
    try {
      const data = JSON.parse(stripFence(art.content)) as Story[] | StoryBundle;
      const stories = Array.isArray(data) ? data : data.stories ?? [];
      const epic = Array.isArray(data) ? null : data.epic ?? null;
      return stories.length ? { stories, epic } : null;
    } catch {
      return null;
    }
  }, [artifacts]);
}

