import { AnimatePresence, motion } from "framer-motion";
import { RotateCcw, MessagesSquare } from "lucide-react";
import type { AgentState } from "../../lib/types";
import AgentChatMessage from "./AgentChatMessage";

interface Props {
  agentOrder: string[];
  agents: Record<string, AgentState>;
  loops: { iteration: number; comments: string[]; final?: boolean }[];
}

/**
 * Chat-style pipeline view (UI_VISUAL_SPEC Screen 03). Renders each agent as a
 * conversation bubble via <AgentChatMessage /> and threads reviewer loop-back
 * banners inline. Pure presentation — the SSE state is owned by useAgentStream.
 */
export default function ChatPipeline({ agentOrder, agents, loops }: Readonly<Props>) {
  if (agentOrder.length === 0) {
    return (
      <div className="grid place-items-center rounded-card border border-white/10 bg-white/[0.02] p-12 text-center">
        <MessagesSquare className="mb-3 h-9 w-9 text-slate-500" />
        <p className="text-sm text-slate-400">
          Describe a feature above and hit <span className="text-slate-200">Run team</span> to
          watch the agents collaborate live.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {agentOrder.map((id) => {
        const agent = agents[id];
        if (!agent) return null;
        const showLoops = id === "reviewer" && loops.length > 0;
        return (
          <div key={id} className="space-y-4">
            <AgentChatMessage agent={agent} />

            <AnimatePresence>
              {showLoops &&
                loops.map((loop) => (
                  <motion.div
                    key={`loop-${loop.iteration}`}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="ml-12 flex items-start gap-2.5 rounded-xl border border-dashed border-review/40 bg-review/[0.06] p-3 text-amber-200"
                  >
                    <RotateCcw className="mt-0.5 h-4 w-4 shrink-0" />
                    <div className="text-xs">
                      <p className="font-semibold">
                        {loop.final
                          ? `Max review iterations reached — Developer applied a final revision (${loop.iteration}) to address the remaining comments.`
                          : `Reviewer requested changes — looping back to the Developer (revision ${loop.iteration}).`}
                      </p>
                      {loop.comments?.length > 0 && (
                        <ul className="mt-1 list-disc space-y-0.5 pl-4 text-amber-200/80">
                          {loop.comments.map((c, idx) => (
                            <li key={`${loop.iteration}-${idx}`}>{c}</li>
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


