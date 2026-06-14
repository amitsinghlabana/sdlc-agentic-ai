import { useMemo } from "react";
import type { Artifact, Story, StoryBundle } from "../lib/types";

/**
 * Parse the `stories.json` artifact (if the Requirements agent produced one)
 * into a StoryBundle for the JIRA push panel. Accepts either a bare array of
 * stories or an object `{ epic, stories }`. Returns null when absent/invalid.
 */
export function useStoryBundle(artifacts: Record<string, Artifact>): StoryBundle | null {
  return useMemo(() => {
    const art = artifacts["stories.json"];
    if (!art) return null;
    try {
      const data = JSON.parse(art.content) as Story[] | StoryBundle;
      const stories = Array.isArray(data) ? data : data.stories ?? [];
      const epic = Array.isArray(data) ? null : data.epic ?? null;
      return stories.length ? { stories, epic } : null;
    } catch {
      return null;
    }
  }, [artifacts]);
}

