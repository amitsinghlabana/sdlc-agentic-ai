import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sparkles, BookOpenText, Ticket, Github, Settings, X } from "lucide-react";
import type { ProviderKey } from "../lib/types";
import { useAdmin } from "../hooks/useAdmin";

type Admin = ReturnType<typeof useAdmin>;

const META: Record<ProviderKey, { label: string; live: string; Icon: typeof Sparkles }> = {
  llm: { label: "LLM", live: "azure", Icon: Sparkles },
  knowledge: { label: "Foundry IQ", live: "foundry", Icon: BookOpenText },
  jira: { label: "JIRA", live: "cloud", Icon: Ticket },
  github: { label: "GitHub", live: "cloud", Icon: Github },
};

interface PanelProps {
  admin: Admin;
  onClose: () => void;
}

function SettingsPanel({ admin, onClose }: Readonly<PanelProps>) {
  const ref = useRef<HTMLDivElement>(null);
  const providers = admin.state?.providers;

  // Close on outside click / Escape.
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: -6, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -6, scale: 0.98 }}
      transition={{ duration: 0.14 }}
      className="absolute right-0 top-12 z-30 w-[340px] rounded-2xl border border-white/10 bg-ink-900/95 p-3 shadow-soft backdrop-blur-xl"
    >
      <div className="mb-2 flex items-center justify-between px-1">
        <p className="text-sm font-semibold text-slate-100">Providers — mock / live</p>
        <button
          onClick={onClose}
          className="rounded-md p-0.5 text-slate-400 hover:text-slate-200"
          title="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="mb-2 px-1 text-[11px] leading-relaxed text-slate-400">
        Switch any integration without a restart. Choices persist; live falls back to mock if
        not configured.
      </p>

      {!providers ? (
        <p className="px-1 py-3 text-xs text-slate-500">Loading…</p>
      ) : (
        (Object.keys(META) as ProviderKey[]).map((key) => {
          const p = providers[key];
          if (!p) return null;
          const { label, live, Icon } = META[key];
          const isLive = p.selected !== "mock";
          const fellBack = isLive && p.effective === "mock";
          return (
            <div
              key={key}
              className="mb-1.5 flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-slate-300" />
                <div>
                  <p className="text-xs font-semibold text-slate-200">{label}</p>
                  <p className="text-[10px] text-slate-500">
                    {p.selected}
                    {fellBack ? " → mock (not configured)" : ""}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-ink-950/60 p-0.5">
                <button
                  disabled={admin.busy}
                  onClick={() => admin.setProvider(`${key}_provider`, "mock")}
                  className={[
                    "rounded-md px-2 py-1 text-[11px] font-semibold transition disabled:opacity-50",
                    !isLive ? "bg-amber-400/20 text-amber-200" : "text-slate-400 hover:text-slate-200",
                  ].join(" ")}
                >
                  Mock
                </button>
                <button
                  disabled={admin.busy}
                  onClick={() => admin.setProvider(`${key}_provider`, live)}
                  className={[
                    "rounded-md px-2 py-1 text-[11px] font-semibold transition disabled:opacity-50",
                    isLive ? "bg-emerald-400/20 text-emerald-200" : "text-slate-400 hover:text-slate-200",
                  ].join(" ")}
                >
                  Live
                </button>
              </div>
            </div>
          );
        })
      )}

      <button
        onClick={admin.reset}
        disabled={admin.busy}
        className="mt-1 w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/[0.07] disabled:opacity-50"
      >
        Reset to .env defaults
      </button>
    </motion.div>
  );
}

/** The gear button + popover, ready to drop into the Header. */
export function SettingsMenu({ admin }: Readonly<{ admin: Admin }>) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        title="Switch providers (mock / live)"
        className={[
          "grid h-8 w-8 place-items-center rounded-lg border transition",
          open
            ? "border-brand-500/50 bg-brand-500/15 text-brand-300"
            : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200",
        ].join(" ")}
      >
        <Settings className="h-4 w-4" />
      </button>
      <AnimatePresence>
        {open && <SettingsPanel admin={admin} onClose={() => setOpen(false)} />}
      </AnimatePresence>
    </div>
  );
}






