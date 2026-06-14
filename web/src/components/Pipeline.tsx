import { AnimatePresence, motion } from "framer-motion";
import { RotateCcw, Workflow } from "lucide-react";
import type { AgentState } from "../lib/types";
import AgentCard from "./AgentCard";

interface Props {
  agentOrder: string[];
  agents: Record<string, AgentState>;
  loops: { iteration: number; comments: string[] }[];
}

export default function Pipeline({ agentOrder, agents, loops }: Props) {
  if (agentOrder.length === 0) {
    return (
      <div className="glass grid place-items-center rounded-2xl p-12 text-center shadow-soft">
        <Workflow className="mb-3 h-9 w-9 text-slate-500" />
        <p className="text-sm text-slate-400">
          Describe a feature above and hit <span className="text-slate-200">Run team</span> to
          watch the agents collaborate live.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {agentOrder.map((id, i) => {
        const agent = agents[id];
        if (!agent) return null;
        const showLoops = id === "reviewer" && loops.length > 0;
        return (
          <div key={id} className="space-y-3">
            {/* connector */}
            {i > 0 && (
              <div className="ml-[26px] h-3 w-px bg-gradient-to-b from-white/15 to-transparent" />
            )}
            <AgentCard agent={agent} />

            <AnimatePresence>
              {showLoops &&
                loops.map((loop) => (
                  <motion.div
                    key={`loop-${loop.iteration}`}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="flex items-start gap-2.5 rounded-xl border border-dashed border-amber-400/40 bg-amber-400/[0.06] p-3 text-amber-200"
                  >
                    <RotateCcw className="mt-0.5 h-4 w-4 shrink-0" />
                    <div className="text-xs">
                      <p className="font-semibold">
                        Reviewer requested changes — looping back to the Developer (revision{" "}
                        {loop.iteration}).
                      </p>
                      {loop.comments?.length > 0 && (
                        <ul className="mt-1 list-disc space-y-0.5 pl-4 text-amber-200/80">
                          {loop.comments.map((c, idx) => (
                            <li key={idx}>{c}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </motion.div>
                ))}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

