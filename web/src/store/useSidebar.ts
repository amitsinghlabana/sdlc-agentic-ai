import { useSyncExternalStore } from "react";

/**
 * Global sidebar collapsed/expanded state.
 *
 * A tiny module-level external store (same pattern as `toast.ts`) backed by
 * localStorage so the choice persists across reloads AND across route changes —
 * each page mounts its own <Sidebar />, so a shared store keeps them in sync.
 */
const KEY = "sdlc:sidebar-collapsed";

function read(): boolean {
  try {
    return localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
}

let collapsed = read();
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

export function setSidebarCollapsed(next: boolean) {
  collapsed = next;
  try {
    localStorage.setItem(KEY, next ? "1" : "0");
  } catch {
    /* storage unavailable — keep in-memory state only */
  }
  emit();
}

export function toggleSidebar() {
  setSidebarCollapsed(!collapsed);
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function useSidebarCollapsed(): boolean {
  return useSyncExternalStore(subscribe, () => collapsed, () => false);
}

