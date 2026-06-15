import { useSyncExternalStore } from "react";

/**
 * Global confirm dialog store (replaces the native, ugly `window.confirm`).
 *
 * A tiny module-level external store, mirroring `toast.ts`. Any module can
 * `await confirm({...})` to get a themed modal; `<ConfirmDialog />` renders it.
 * The returned promise resolves to `true` (confirmed) or `false` (cancelled).
 */
export type ConfirmTone = "default" | "danger";

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ConfirmTone;
}

export interface ConfirmState extends ConfirmOptions {
  id: string;
  open: boolean;
}

let state: ConfirmState | null = null;
let resolver: ((v: boolean) => void) | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

function newId(): string {
  try {
    return globalThis.crypto.randomUUID();
  } catch {
    return "c" + Math.random().toString(36).slice(2, 10);
  }
}

/** Open a themed confirm dialog; resolves true/false. Pass a string for a quick prompt. */
export function confirm(opts: ConfirmOptions | string): Promise<boolean> {
  const options: ConfirmOptions = typeof opts === "string" ? { message: opts } : opts;
  // If a dialog is already open, cancel it before showing the new one.
  if (resolver) {
    resolver(false);
    resolver = null;
  }
  state = { id: newId(), open: true, ...options };
  emit();
  return new Promise<boolean>((resolve) => {
    resolver = resolve;
  });
}

/** Resolve the open dialog and start its close animation. Called by the UI. */
export function resolveConfirm(value: boolean) {
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

export function useConfirmState(): ConfirmState | null {
  return useSyncExternalStore(subscribe, () => state);
}

