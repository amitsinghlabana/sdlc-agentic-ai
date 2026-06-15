import { useMemo, useState } from "react";
import { ArrowLeft, Play, Search, Trash2 } from "lucide-react";
import { Link } from "../lib/router";
import { useRuns, clearRuns, type RunRecord } from "../store/useRunStore";
import { toast } from "../store/toast";
import RunStatusBadge from "../components/runs/RunStatusBadge";
import EmptyState from "../components/dashboard/EmptyState";
import TopBar from "../components/shell/TopBar";

type Filter = "all" | RunRecord["status"];

const FILTERS: { key: Filter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "done", label: "Done" },
  { key: "error", label: "Error" },
  { key: "stopped", label: "Stopped" },
];

function fmtDuration(ms: number | null): string {
  return ms == null ? "—" : `${(ms / 1000).toFixed(1)}s`;
}

function fmtWhen(ts: number): string {
  return new Date(ts).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function RunsHistory() {
  const runs = useRuns();
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return runs.filter(
      (r) =>
        (filter === "all" || r.status === filter) &&
        (!q || r.request.toLowerCase().includes(q) || (r.repo ?? "").toLowerCase().includes(q)),
    );
  }, [runs, filter, query]);


  return (
    <div className="relative min-h-full">
      <TopBar
        maxWidth="max-w-[1100px]"
        showBrand={false}
        left={<span className="text-sm font-semibold text-slate-200">Runs</span>}
        right={
          <Link
            to="/app"
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-b from-accent-500 to-accent-600 px-4 py-2 text-sm font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5"
          >
            <Play className="h-4 w-4" /> New run
          </Link>
        }
      />

      <main className="mx-auto max-w-[1100px] px-6 py-8">
        <Link
          to="/dashboard"
          className="mb-4 inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 transition hover:text-slate-200"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Dashboard
        </Link>

        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Runs history</h1>
            <p className="mt-1 text-slate-400">Every pipeline run, with status and duration.</p>
          </div>
          {runs.length > 0 && (
            <button
              onClick={() => {
                clearRuns();
                toast("Run history cleared");
              }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-400 transition hover:text-rose-300"
            >
              <Trash2 className="h-3.5 w-3.5" /> Clear history
            </button>
          )}
        </div>

        {runs.length === 0 ? (
          <EmptyState
            title="No runs yet"
            body="Describe a feature and watch six agents design, build, review, and ship it — live."
            cta={{ to: "/app", label: "Start your first run" }}
          />
        ) : (
          <>
            {/* Controls */}
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1 rounded-xl border border-white/10 bg-white/[0.03] p-1">
                {FILTERS.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setFilter(f.key)}
                    className={[
                      "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                      filter === f.key ? "bg-accent-500/20 text-accent-200" : "text-slate-400 hover:text-slate-200",
                    ].join(" ")}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
              <div className="relative flex-1 min-w-[180px]">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search requests or repos…"
                  className="w-full rounded-xl border border-white/10 bg-white/[0.03] py-2 pl-9 pr-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-accent-500/50 focus:outline-none"
                />
              </div>
            </div>

            {/* Table */}
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02]">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Request</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold">Duration</th>
                    <th className="px-4 py-3 font-semibold">Files</th>
                    <th className="hidden px-4 py-3 font-semibold md:table-cell">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => (
                    <tr
                      key={r.id}
                      className="border-b border-white/5 transition hover:bg-white/[0.03]"
                    >
                      <td className="max-w-[320px] px-4 py-3">
                        <p className="truncate font-medium text-slate-100">{r.request}</p>
                        {r.repo && <p className="truncate text-xs text-slate-500">{r.repo}</p>}
                      </td>
                      <td className="px-4 py-3"><RunStatusBadge status={r.status} /></td>
                      <td className="px-4 py-3 text-slate-300">{fmtDuration(r.durationMs)}</td>
                      <td className="px-4 py-3 text-slate-300">{r.artifacts}</td>
                      <td className="hidden px-4 py-3 text-slate-400 md:table-cell">{fmtWhen(r.startedAt)}</td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-10 text-center text-sm text-slate-500">
                        No runs match the current filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Showing {filtered.length} of {runs.length} run{runs.length === 1 ? "" : "s"}.
            </p>
          </>
        )}
      </main>
    </div>
  );
}


