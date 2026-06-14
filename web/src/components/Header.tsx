import { Sparkles, Clock } from "lucide-react";
import type { AppConfig, RunStatus } from "../lib/types";
import { SettingsMenu } from "./SettingsPanel";
import TopBar from "./shell/TopBar";
import type { useAdmin } from "../hooks/useAdmin";

/** Status indicator dot color per run state (mirrors the legacy header). */
const DOT_COLOR: Record<RunStatus, string> = {
  idle: "bg-slate-600",
  running: "animate-pulse bg-brand-400",
  done: "bg-emerald-400",
  stopped: "bg-amber-400",
  error: "bg-rose-400",
};

interface Props {
  config: AppConfig | null;
  providerLabel: string | null;
  runStatus: RunStatus;
  durationMs: number | null;
  admin: ReturnType<typeof useAdmin>;
}

export default function Header({ config, providerLabel, runStatus, durationMs, admin }: Readonly<Props>) {
  const isMock = config?.is_mock ?? true;
  const label = providerLabel ?? config?.provider_label ?? "…";

  return (
    <TopBar
      maxWidth="max-w-[1400px]"
      subtitle="requirements → design → code → tests → review → docs"
      right={
        <>
          {durationMs != null && (
            <span className="hidden items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 sm:flex">
              <Clock className="h-3.5 w-3.5" />
              {(durationMs / 1000).toFixed(1)}s
            </span>
          )}
          <span
            title={
              isMock
                ? "Running on the free mock provider — no tokens spent."
                : "Running on a live LLM provider."
            }
            className={[
              "flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold",
              isMock
                ? "border-amber-400/40 bg-amber-400/10 text-amber-300"
                : "border-emerald-400/40 bg-emerald-400/10 text-emerald-300",
            ].join(" ")}
          >
            <Sparkles className="h-3.5 w-3.5" />
            {label}
          </span>
          <span
            className={["h-2.5 w-2.5 rounded-full", DOT_COLOR[runStatus]].join(" ")}
          />
          <SettingsMenu admin={admin} />
        </>
      }
    />
  );
}

