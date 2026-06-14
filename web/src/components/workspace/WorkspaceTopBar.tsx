import { Boxes, GitPullRequest, Play, RotateCcw, Square } from "lucide-react";
import { Link } from "../../lib/router";
import type { AdminState, RunStatus } from "../../lib/types";
import type { JiraStatus } from "../../hooks/useJira";
import { SettingsMenu } from "../SettingsPanel";
import type { useAdmin } from "../../hooks/useAdmin";
import ProviderBadges from "./ProviderBadges";

interface GitHubStatusLite {
  is_mock: boolean;
  owner?: string;
  repo?: string;
  has_default_repo?: boolean;
}

interface Props {
  runStatus: RunStatus;
  durationMs: number | null;
  running: boolean;
  onRun: () => void;
  onStop: () => void;
  onRetry: () => void;
  canRetry: boolean;
  onPublish: () => void;
  publishCount: number;
  admin: ReturnType<typeof useAdmin>;
  adminState: AdminState | null;
  github: GitHubStatusLite | null;
  jira: JiraStatus | null;
  llmLabel: string;
}

const STATUS_META: Record<RunStatus, { dot: string; label: string }> = {
  idle: { dot: "bg-slate-600", label: "Idle" },
  running: { dot: "animate-pulse bg-accent-400", label: "Running" },
  done: { dot: "bg-emerald-400", label: "Done" },
  stopped: { dot: "bg-amber-400", label: "Stopped" },
  error: { dot: "bg-rose-400", label: "Error" },
};

/**
 * Sticky workspace top bar (UI_SPEC §3): project + branch selectors, live run
 * status + timer, Run / Stop / Retry controls, a Publish button (with the
 * selected-file count) and the integration status badges + provider switcher.
 */
export default function WorkspaceTopBar({
  runStatus,
  durationMs,
  running,
  onRun,
  onStop,
  onRetry,
  canRetry,
  onPublish,
  publishCount,
  admin,
  adminState,
  github,
  jira,
  llmLabel,
}: Readonly<Props>) {
  const status = STATUS_META[runStatus];

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-white/10 bg-ink-950/70 px-4 backdrop-blur-xl">
      {/* Brand — small screens only; the shared Sidebar owns it on lg+ */}
      <Link
        to="/"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-accent-500 to-accent-600 shadow-glow-accent lg:hidden"
      >
        <Boxes className="h-5 w-5 text-white" />
      </Link>


      {/* Status */}
      <span className="hidden items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-xs text-slate-300 lg:flex">
        <span className={["h-2 w-2 rounded-full", status.dot].join(" ")} />
        {status.label}
        {durationMs != null && <span className="text-slate-500">· {(durationMs / 1000).toFixed(1)}s</span>}
      </span>

      <div className="flex-1" />

      {/* Integration badges */}
      <ProviderBadges admin={adminState} github={github} jira={jira} llmLabel={llmLabel} />

      {/* Run controls */}
      <div className="flex items-center gap-1.5">
        <button
          onClick={onRun}
          disabled={running}
          title="Run pipeline"
          className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-b from-accent-500 to-accent-600 px-3 py-1.5 text-xs font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5 disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5" /> Run
        </button>
        <button
          onClick={onStop}
          disabled={!running}
          title="Stop"
          className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 bg-white/[0.03] text-slate-300 transition hover:bg-white/[0.07] disabled:opacity-40"
        >
          <Square className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={onRetry}
          disabled={running || !canRetry}
          title="Retry last run"
          className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 bg-white/[0.03] text-slate-300 transition hover:bg-white/[0.07] disabled:opacity-40"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Publish */}
      <button
        onClick={onPublish}
        disabled={publishCount === 0}
        title={publishCount === 0 ? "Select files in the explorer to publish" : "Publish selected files"}
        className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-400/40 bg-indigo-400/15 px-3 py-1.5 text-xs font-semibold text-indigo-200 transition hover:bg-indigo-400/25 disabled:opacity-50"
      >
        <GitPullRequest className="h-3.5 w-3.5" /> Publish
        {publishCount > 0 && (
          <span className="rounded-full bg-indigo-400/30 px-1.5 text-[10px]">{publishCount}</span>
        )}
      </button>

      <SettingsMenu admin={admin} />
    </header>
  );
}

