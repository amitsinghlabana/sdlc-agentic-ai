import { Fragment } from "react";
import { motion } from "framer-motion";
import type { AgentState } from "../../lib/types";

interface Props {
  agentOrder: string[];
  agents: Record<string, AgentState>;
}

const STATE_META: Record<AgentState["status"], { dot: string; ring: string; text: string }> = {
  queued: { dot: "bg-slate-600", ring: "border-white/10", text: "text-slate-400" },
  working: { dot: "bg-accent-400 animate-pulse", ring: "border-accent-500/60 shadow-glow-sm", text: "text-accent-200" },
  done: { dot: "bg-emerald-400", ring: "border-emerald-400/40", text: "text-emerald-200" },
  approved: { dot: "bg-emerald-400", ring: "border-emerald-400/40", text: "text-emerald-200" },
  changes: { dot: "bg-review", ring: "border-review/50", text: "text-amber-200" },
  error: { dot: "bg-rose-400", ring: "border-rose-400/50", text: "text-rose-200" },
};

/**
 * Compact horizontal step tracker (UI_SPEC §6.1):
 * Requirements → Architect → Developer → … — each node reflects its agent's
 * live status (queued / working / done / changes / error). Derived purely from
 * the SSE-fed agents map, so it stays in lock-step with the activity feed.
 */
export default function PipelineTracker({ agentOrder, agents }: Readonly<Props>) {
  if (agentOrder.length === 0) return null;

  return (
    <div className="flex items-center gap-1 overflow-x-auto rounded-card border border-white/10 bg-white/[0.03] p-3">
      {agentOrder.map((id, i) => {
        const agent = agents[id];
        if (!agent) return null;
        const meta = STATE_META[agent.status];
        return (
          <Fragment key={id}>
            {i > 0 && <div className="h-px w-4 shrink-0 bg-white/15 sm:w-6" />}
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(i * 0.04, 0.3) }}
              title={`${agent.name} — ${agent.status}`}
              className={[
                "flex shrink-0 items-center gap-1.5 rounded-pill border px-2.5 py-1",
                meta.ring,
              ].join(" ")}
            >
              <span className={["h-1.5 w-1.5 rounded-full", meta.dot].join(" ")} />
              <span className="text-sm leading-none">{agent.emoji}</span>
              <span className={["text-[11px] font-semibold", meta.text].join(" ")}>
                {agent.name}
              </span>
              {agent.iteration > 0 && (
                <span className="rounded bg-white/10 px-1 text-[9px] font-semibold text-slate-300">
                  v{agent.iteration}
                </span>
              )}
            </motion.div>
          </Fragment>
        );
      })}
    </div>
  );
}

