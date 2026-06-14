import { useCallback, useEffect, useState } from "react";
import type { AdminState, ProviderKey } from "../lib/types";

/**
 * Runtime provider switching (mock ↔ live) via /api/admin/providers.
 * Choices persist server-side (runtime-config) and hot-reload the matching
 * client — no restart, no commit.
 */
export function useAdmin(notify?: (msg: string) => void) {
  const [state, setState] = useState<AdminState | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    fetch("/api/admin/providers")
      .then((r) => r.json())
      .then(setState)
      .catch(() => setState(null));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const setProvider = useCallback(
    async (key: string, value: string) => {
      if (busy) return;
      const pkey = key.replace("_provider", "") as ProviderKey;

      // Optimistically reflect the choice so the toggle flips instantly — the
      // server response then reconciles `effective` (in case live falls back
      // to mock when a provider isn't configured).
      setState((prev) =>
        prev?.providers[pkey]
          ? {
              ...prev,
              providers: {
                ...prev.providers,
                [pkey]: { ...prev.providers[pkey], selected: value },
              },
            }
          : prev,
      );
      setBusy(true);
      try {
        const r = await fetch("/api/admin/providers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [key]: value }),
        });
        if (!r.ok) {
          const detail = (await r.json().catch(() => ({})))?.detail;
          throw new Error(detail || `HTTP ${r.status}`);
        }
        setState((await r.json()) as AdminState);
        notify?.(`Switched ${pkey} → ${value}`);
      } catch (e) {
        notify?.("Switch failed: " + (e as Error).message);
        refresh(); // roll back optimistic state to server truth
      } finally {
        setBusy(false);
      }
    },
    [busy, notify, refresh],
  );

  const reset = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await fetch("/api/admin/providers/reset", { method: "POST" });
      setState((await r.json()) as AdminState);
      notify?.("Reverted to .env defaults");
    } catch (e) {
      notify?.("Reset failed: " + (e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [busy, notify]);

  return { state, busy, setProvider, reset, refresh };
}

