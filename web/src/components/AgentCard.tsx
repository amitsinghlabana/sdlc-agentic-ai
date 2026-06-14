import { motion } from "framer-motion";
import { Check, Loader2, RotateCcw, AlertTriangle, Circle } from "lucide-react";
import type { AgentState } from "../lib/types";

const STATUS_META: Record<
  AgentState["status"],
  { label: string; cls: string; icon: JSX.Element }
> = {
  queued: {
    label: "queued",
    cls: "text-slate-400 border-white/10",
    icon: <Circle className="h-3 w-3" />,
  },
  working: {
    label: "working",
    cls: "text-brand-300 border-brand-500/50",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  done: {
    label: "done",
    cls: "text-emerald-300 border-emerald-400/40",
    icon: <Check className="h-3 w-3" />,
  },
  approved: {
    label: "approved",
    cls: "text-emerald-300 border-emerald-400/40",
    icon: <Check className="h-3 w-3" />,
  },
  changes: {
    label: "changes requested",
    cls: "text-amber-300 border-amber-400/40",
    icon: <RotateCcw className="h-3 w-3" />,
  },
  error: {
    label: "error",
    cls: "text-rose-300 border-rose-400/40",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
};

export default function AgentCard({ agent }: { agent: AgentState }) {
  const meta = STATUS_META[agent.status];
  const working = agent.status === "working";
  const active = working || agent.status !== "queued";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: active ? 1 : 0.62, y: 0 }}
      transition={{ duration: 0.3 }}
      className={[
        "glass rounded-2xl p-4 transition-shadow duration-300",
        working ? "shadow-glow ring-1 ring-brand-500/50" : "shadow-soft",
      ].join(" ")}
    >
      <div className="flex items-center gap-3">
        <div
          className={[
            "grid h-11 w-11 shrink-0 place-items-center rounded-xl border text-xl",
            working
              ? "border-brand-500/60 bg-brand-500/15 animate-pulse-ring"
              : "border-white/10 bg-white/[0.04]",
          ].join(" ")}
        >
          {agent.emoji}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-semibold text-slate-100">{agent.name}</h3>
            {agent.iteration > 0 && (
              <span className="rounded-full border border-brand-500/40 bg-brand-500/15 px-2 py-0.5 text-[10px] font-semibold text-brand-300">
                revision {agent.iteration}
              </span>
            )}
          </div>
          <p className="truncate text-xs text-slate-400">{agent.role}</p>
        </div>

        <span
          className={[
            "flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold",
            meta.cls,
          ].join(" ")}
        >
          {meta.icon}
          {meta.label}
        </span>
      </div>

      {(working || agent.stream) && (
        <div
          className={[
            "mt-3 max-h-56 overflow-auto whitespace-pre-wrap rounded-xl border border-white/5 bg-ink-950/50 p-3 text-[13px] leading-relaxed text-slate-300",
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
    </motion.div>
  );
}

