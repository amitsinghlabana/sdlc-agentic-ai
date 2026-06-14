import { Sparkles, BookOpenText, Ticket, Github, RotateCcw } from "lucide-react";
import type { ProviderKey } from "../../lib/types";
import type { useAdmin } from "../../hooks/useAdmin";

type Admin = ReturnType<typeof useAdmin>;

const META: Record<
  ProviderKey,
  { label: string; live: string; sub: string; Icon: typeof Sparkles }
> = {
  llm: { label: "LLM Provider", live: "azure", sub: "Azure OpenAI", Icon: Sparkles },
  knowledge: { label: "Foundry IQ", live: "foundry", sub: "Knowledge retrieval", Icon: BookOpenText },
  jira: { label: "JIRA", live: "cloud", sub: "Issue tracking", Icon: Ticket },
  github: { label: "GitHub", live: "cloud", sub: "Source control", Icon: Github },
};

/**
 * Full-page provider configuration cards for the Settings → Providers tab.
 * Reuses the existing useAdmin hook (mock ↔ live switching, persisted
 * server-side) so there is a single source of truth with the header popover.
 */
export default function ProviderSettingForm({ admin }: Readonly<{ admin: Admin }>) {
  const providers = admin.state?.providers;

  if (!providers) {
    return <p className="px-1 py-6 text-sm text-slate-500">Loading providers…</p>;
  }

  return (
    <div className="space-y-3">
      {(Object.keys(META) as ProviderKey[]).map((key) => {
        const p = providers[key];
        if (!p) return null;
        const { label, live, sub, Icon } = META[key];
        const isLive = p.selected !== "mock";
        const fellBack = isLive && p.effective === "mock";

        return (
          <div
            key={key}
            className="flex items-center justify-between gap-4 rounded-card border border-white/10 bg-white/[0.03] p-4 transition hover:border-white/20"
          >
            <div className="flex min-w-0 items-center gap-3">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.04]">
                <Icon className="h-5 w-5 text-accent-400" />
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-100">{label}</p>
                <p className="truncate text-xs text-slate-500">
                  {sub} · <span className="font-mono">{p.selected}</span>
                  {fellBack ? " → mock (not configured)" : ""}
                </p>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-3">
              <span
                className={[
                  "rounded-pill px-2.5 py-1 text-xs font-semibold",
                  isLive && !fellBack
                    ? "bg-success/15 text-success"
                    : "bg-warning/15 text-warning",
                ].join(" ")}
              >
                {isLive && !fellBack ? "● Live" : "○ Mock"}
              </span>
              <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-ink-950/60 p-0.5">
                <button
                  disabled={admin.busy}
                  onClick={() => admin.setProvider(`${key}_provider`, "mock")}
                  className={[
                    "rounded-md px-2.5 py-1 text-[11px] font-semibold transition disabled:opacity-50",
                    isLive ? "text-slate-400 hover:text-slate-200" : "bg-amber-400/20 text-amber-200",
                  ].join(" ")}
                >
                  Mock
                </button>
                <button
                  disabled={admin.busy}
                  onClick={() => admin.setProvider(`${key}_provider`, live)}
                  className={[
                    "rounded-md px-2.5 py-1 text-[11px] font-semibold transition disabled:opacity-50",
                    isLive ? "bg-emerald-400/20 text-emerald-200" : "text-slate-400 hover:text-slate-200",
                  ].join(" ")}
                >
                  Live
                </button>
              </div>
            </div>
          </div>
        );
      })}

      <button
        onClick={admin.reset}
        disabled={admin.busy}
        className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-semibold text-slate-300 transition hover:bg-white/[0.07] disabled:opacity-50"
      >
        <RotateCcw className="h-3.5 w-3.5" />
        Reset to .env defaults
      </button>
    </div>
  );
}


