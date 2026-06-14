import { motion } from "framer-motion";
import { Check, Loader2, RotateCcw, AlertTriangle, Circle } from "lucide-react";
import type { AgentState } from "../../lib/types";

const STATUS_META: Record<
  AgentState["status"],
  { label: string; cls: string; icon: JSX.Element }
> = {
  queued: {
    label: "Queued",
    cls: "text-slate-400 bg-white/10",
    icon: <Circle className="h-3 w-3" />,
  },
  working: {
    label: "Working",
    cls: "text-accent-300 bg-accent-500/15",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  done: {
    label: "Done",
    cls: "text-emerald-300 bg-emerald-400/15",
    icon: <Check className="h-3 w-3" />,
  },
  approved: {
    label: "Approved",
    cls: "text-emerald-300 bg-emerald-400/15",
    icon: <Check className="h-3 w-3" />,
  },
  changes: {
    label: "Changes",
    cls: "text-review bg-review/15",
    icon: <RotateCcw className="h-3 w-3" />,
  },
  error: {
    label: "Error",
    cls: "text-rose-300 bg-rose-400/15",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
};

/**
 * Chat-style agent message (UI_VISUAL_SPEC Screen 03). Each agent is rendered
 * as a conversation bubble: avatar on the left, name + status + streaming
 * output in a glass bubble. The active agent gets an accent glow + pulse.
 */
export default function AgentChatMessage({ agent }: Readonly<{ agent: AgentState }>) {
  const meta = STATUS_META[agent.status];
  const working = agent.status === "working";
  const queued = agent.status === "queued";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: queued ? 0.6 : 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex gap-3"
    >
      {/* Avatar */}
      <div
        className={[
          "grid h-10 w-10 shrink-0 place-items-center rounded-xl border text-lg",
          working
            ? "border-accent-500/60 bg-accent-500/15 animate-pulse-ring"
            : "border-white/10 bg-white/[0.04]",
        ].join(" ")}
      >
        {agent.emoji}
      </div>

      {/* Bubble */}
      <div
        className={[
          "min-w-0 flex-1 rounded-card border p-3.5 transition-shadow duration-300",
          working
            ? "border-accent-500/40 bg-accent-500/[0.06] shadow-glow-sm"
            : "border-white/10 bg-white/[0.03]",
        ].join(" ")}
      >
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="truncate text-sm font-semibold text-slate-100">{agent.name}</h3>
          {agent.iteration > 0 && (
            <span className="rounded-pill border border-accent-500/40 bg-accent-500/15 px-2 py-0.5 text-[10px] font-semibold text-accent-300">
              revision {agent.iteration}
            </span>
          )}
          <span
            className={[
              "ml-auto inline-flex items-center gap-1.5 rounded-pill px-2.5 py-1 text-[11px] font-semibold",
              meta.cls,
            ].join(" ")}
          >
            {meta.icon}
            {meta.label}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-slate-500">{agent.role}</p>

        {(working || agent.stream) && (
          <div
            className={[
              "mt-3 max-h-60 overflow-auto whitespace-pre-wrap rounded-xl border border-white/5 bg-ink-950/50 p-3 text-[13px] leading-relaxed text-slate-300",
              working ? "cursor-blink" : "",
            ].join(" ")}
          >
            {agent.stream}
          </div>
        )}

        {agent.summary && (
          <p className="mt-2.5 flex items-start gap-1.5 text-xs text-emerald-300/90">
            <Check className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>{agent.summary}</span>
          </p>
        )}
      </div>
    </motion.div>
  );
}

