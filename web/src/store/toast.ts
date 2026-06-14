import { useSyncExternalStore } from "react";

/**
 * Global toast store (no `sonner` — it's network-blocked here).
 *
 * A tiny module-level external store so any module can fire a toast via the
 * standalone `toast()` function, and `<ToastViewport />` renders them. Mirrors
 * the sonner API surface we actually use.
 */
export type ToastTone = "info" | "success" | "error";

export interface Toast {
  id: string;
  message: string;
  tone: ToastTone;
}

let toasts: Toast[] = [];
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

function newId(): string {
  try {
    return globalThis.crypto.randomUUID();
  } catch {
    return "t" + Math.random().toString(36).slice(2, 10);
  }
}

export function dismissToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id);
  emit();
}

export function toast(message: string, tone: ToastTone = "info", ttl = 2800) {
  const id = newId();
  toasts = [...toasts, { id, message, tone }];
  emit();
  if (ttl > 0) globalThis.setTimeout(() => dismissToast(id), ttl);
  return id;
}

toast.success = (m: string, ttl?: number) => toast(m, "success", ttl);
toast.error = (m: string, ttl?: number) => toast(m, "error", ttl);

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function useToasts(): Toast[] {
  return useSyncExternalStore(subscribe, () => toasts);
}

