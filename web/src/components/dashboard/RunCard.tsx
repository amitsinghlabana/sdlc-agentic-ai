import { motion } from "framer-motion";
import { ArrowRight, Clock, FileCode2, FolderGit2 } from "lucide-react";
import { Link } from "../../lib/router";
import type { RunRecord } from "../../store/useRunStore";

const STATUS: Record<RunRecord["status"], { label: string; cls: string }> = {
  done: { label: "done", cls: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300" },
  error: { label: "error", cls: "border-rose-400/40 bg-rose-400/10 text-rose-300" },
  stopped: { label: "stopped", cls: "border-amber-400/40 bg-amber-400/10 text-amber-300" },
};

function timeAgo(ts: number): string {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function fmtDuration(ms: number | null): string {
  return ms == null ? "—" : `${(ms / 1000).toFixed(1)}s`;
}

export default function RunCard({ run, delay = 0 }: Readonly<{ run: RunRecord; delay?: number }>) {
  const status = STATUS[run.status];
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, delay }}
      className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl transition hover:border-accent/40 hover:bg-white/[0.05]"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span
            className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${status.cls}`}
          >
            {status.label}
          </span>
          <p className="truncate font-medium text-slate-100">{run.request}</p>
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3 w-3" /> {fmtDuration(run.durationMs)}
          </span>
          <span className="inline-flex items-center gap-1">
            <FileCode2 className="h-3 w-3" /> {run.artifacts} file{run.artifacts === 1 ? "" : "s"}
          </span>
          {run.repo && (
            <span className="inline-flex items-center gap-1 truncate">
              <FolderGit2 className="h-3 w-3" /> {run.repo}
            </span>
          )}
          {run.provider && <span className="truncate">{run.provider}</span>}
          <span>{timeAgo(run.startedAt)}</span>
        </div>
      </div>
      <Link
        to="/app"
        className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-semibold text-slate-200 opacity-0 transition group-hover:opacity-100 hover:bg-white/[0.08]"
      >
        Open <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </motion.div>
  );
}

