import { useSyncExternalStore } from "react";

/**
 * Global text-prompt dialog store (a themed replacement for `window.prompt`).
 *
 * Mirrors `confirm.ts`: any module can `await promptText({...})` to get a themed
 * input modal; `<PromptDialog />` renders it. Resolves to the entered string, or
 * `null` if the user cancelled.
 */
export interface PromptOptions {
  title?: string;
  message?: string;
  defaultValue?: string;
  placeholder?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Optional suffix shown after the input (e.g. ".zip"). */
  suffix?: string;
}

export interface PromptState extends PromptOptions {
  id: string;
  open: boolean;
}

let state: PromptState | null = null;
let resolver: ((v: string | null) => void) | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

function newId(): string {
  try {
    return globalThis.crypto.randomUUID();
  } catch {
    return "p" + Math.random().toString(36).slice(2, 10);
  }
}

/** Open a themed prompt dialog; resolves to the entered value, or null if cancelled. */
export function promptText(opts: PromptOptions | string): Promise<string | null> {
  const options: PromptOptions = typeof opts === "string" ? { message: opts } : opts;
  // If a dialog is already open, cancel it before showing the new one.
  if (resolver) {
    resolver(null);
    resolver = null;
  }
  state = { id: newId(), open: true, ...options };
  emit();
  return new Promise<string | null>((resolve) => {
    resolver = resolve;
  });
}

/** Resolve the open dialog and start its close animation. Called by the UI. */
export function resolvePrompt(value: string | null) {
  if (resolver) {
    resolver(value);
    resolver = null;
  }
  state = state ? { ...state, open: false } : null;
  emit();
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function usePromptState(): PromptState | null {
  return useSyncExternalStore(subscribe, () => state);
}

