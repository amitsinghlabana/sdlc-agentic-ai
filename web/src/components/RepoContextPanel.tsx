import { motion } from "framer-motion";
import { GitBranch } from "lucide-react";
import type { RepoContext } from "../lib/types";

/**
 * Shows the existing-repo files that were read and handed to the agents as
 * context to edit in place (P3: "edit an existing repo").
 */
export default function RepoContextPanel({ ctx }: Readonly<{ ctx: RepoContext }>) {
  const list = ctx.files ?? [];
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-indigo-400/30 bg-indigo-400/[0.06] p-4 shadow-soft"
    >
      <div className="flex items-center gap-2.5">
        <div className="grid h-9 w-9 place-items-center rounded-lg border border-indigo-400/40 bg-indigo-400/15 text-indigo-300">
          <GitBranch className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-100">
            {ctx.error ? "Could not load repository" : `Editing existing repo · ${ctx.repo}`}
            {!ctx.error && (
              <span className="text-slate-400">
                {" "}
                · {list.length} file{list.length === 1 ? "" : "s"} loaded
              </span>
            )}
          </p>
          <p className="text-xs text-slate-400">
            {ctx.error
              ? ctx.error
              : "Read from the repo and given to the agents as context to edit in place — the result publishes as a branch + PR."}
          </p>
        </div>
      </div>

      {!ctx.error && list.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {list.map((f) => (
            <span
              key={f.path}
              className="inline-flex items-center gap-1 rounded border border-indigo-400/30 bg-indigo-400/10 px-1.5 py-0.5 font-mono text-[10px] text-indigo-200"
            >
              {f.path}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

