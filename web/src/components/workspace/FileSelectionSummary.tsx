import { GitPullRequest, X } from "lucide-react";
import type { Artifact } from "../../lib/types";

interface Props {
  files: Artifact[];
  onClear: () => void;
  onRemove: (name: string) => void;
  onPublish: () => void;
  publishing: boolean;
}

/**
 * Sticky "selected for GitHub" summary (UI_SPEC §11). Keeps the publish set
 * always visible so nothing is shipped without explicit user choice. Opens the
 * PublishDrawer rather than auto-pushing.
 */
export default function FileSelectionSummary({
  files,
  onClear,
  onRemove,
  onPublish,
  publishing,
}: Readonly<Props>) {
  if (files.length === 0) return null;

  return (
    <div className="rounded-card border border-indigo-400/30 bg-indigo-400/[0.08] p-3 shadow-soft backdrop-blur-xl">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-100">
          Selected for GitHub <span className="text-indigo-300">({files.length})</span>
        </p>
        <button
          onClick={onClear}
          className="text-[11px] font-medium text-slate-400 transition hover:text-slate-200"
        >
          Clear
        </button>
      </div>

      <div className="mb-3 flex max-h-24 flex-wrap gap-1.5 overflow-auto">
        {files.map((f) => (
          <span
            key={f.name}
            className="inline-flex items-center gap-1 rounded border border-white/10 bg-white/[0.04] px-1.5 py-0.5 font-mono text-[10px] text-slate-200"
          >
            <span className="max-w-[160px] truncate" title={f.name}>
              {f.name}
            </span>
            <button
              onClick={() => onRemove(f.name)}
              className="text-slate-500 transition hover:text-rose-300"
              aria-label={`Remove ${f.name}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>

      <button
        onClick={onPublish}
        disabled={publishing}
        className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-b from-accent-500 to-accent-600 px-3.5 py-2 text-sm font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5 disabled:opacity-50"
      >
        <GitPullRequest className="h-4 w-4" />
        Publish selected to GitHub
      </button>
    </div>
  );
}

