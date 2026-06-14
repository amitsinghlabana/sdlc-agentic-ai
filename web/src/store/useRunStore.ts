import { useSyncExternalStore } from "react";
import type { RunStatus } from "../lib/types";

/**
 * Lightweight run history store (no zustand — it's network-blocked here).
 *
 * A tiny module-level external store backed by localStorage, exposed via
 * useSyncExternalStore. The Workspace records each completed run; the Dashboard
 * reads them for stats + the recent-runs list. Seeds a few realistic demo runs
 * on first load so the dashboard looks alive before the first real run.
 */
export interface RunRecord {
  id: string;
  request: string;
  status: Extract<RunStatus, "done" | "stopped" | "error">;
  durationMs: number | null;
  artifacts: number;
  provider: string | null;
  repo: string | null;
  startedAt: number; // epoch ms
}

const KEY = "sdlc.runs.v1";
const SEED_FLAG = "sdlc.runs.seeded.v1";

export function rid(): string {
  try {
    return globalThis.crypto.randomUUID();
  } catch {
    return "r" + Math.random().toString(36).slice(2, 10);
  }
}

function readStore(): RunRecord[] {
  try {
    const raw = globalThis.localStorage?.getItem(KEY);
    if (raw) return JSON.parse(raw) as RunRecord[];
  } catch {
    /* ignore corrupt/unavailable storage */
  }
  return [];
}

function persist() {
  try {
    globalThis.localStorage?.setItem(KEY, JSON.stringify(runs));
  } catch {
    /* ignore */
  }
}

function demoRuns(): RunRecord[] {
  const now = Date.now();
  const hr = 3_600_000;
  const day = 86_400_000;
  return [
    {
      id: rid(),
      request: "Add email/password login to my web app",
      status: "done",
      durationMs: 41200,
      artifacts: 6,
      provider: "Azure OpenAI · gpt-4.1-mini",
      repo: "amitsinghlabana/sdlc-sandbox",
      startedAt: now - 2 * hr,
    },
    {
      id: rid(),
      request: "Add a REST endpoint to create and list todo items",
      status: "done",
      durationMs: 33800,
      artifacts: 5,
      provider: "Azure OpenAI · gpt-4.1-mini",
      repo: null,
      startedAt: now - day,
    },
    {
      id: rid(),
      request: "Add a contact form that emails the site owner",
      status: "error",
      durationMs: 12100,
      artifacts: 1,
      provider: "Mock",
      repo: null,
      startedAt: now - 2 * day - 3 * hr,
    },
  ];
}

function loadInitial(): RunRecord[] {
  const existing = readStore();
  if (existing.length > 0) return existing;
  try {
    if (globalThis.localStorage?.getItem(SEED_FLAG)) return [];
    const seeded = demoRuns();
    globalThis.localStorage?.setItem(KEY, JSON.stringify(seeded));
    globalThis.localStorage?.setItem(SEED_FLAG, "1");
    return seeded;
  } catch {
    return demoRuns();
  }
}

let runs: RunRecord[] = loadInitial();
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

export function addRun(record: RunRecord) {
  runs = [record, ...runs].slice(0, 50);
  persist();
  emit();
}

export function clearRuns() {
  runs = [];
  persist();
  emit();
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function useRuns(): RunRecord[] {
  return useSyncExternalStore(subscribe, () => runs);
}

