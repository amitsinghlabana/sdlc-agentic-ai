import { useMemo } from "react";
import { motion } from "framer-motion";
import { Activity, ArrowRight, CheckCircle2, Clock, FileCode2, Plus, Search } from "lucide-react";
import { Link } from "../lib/router";
import { useRuns } from "../store/useRunStore";
import StatCard from "../components/dashboard/StatCard";
import RunCard from "../components/dashboard/RunCard";
import EmptyState from "../components/dashboard/EmptyState";
import TopBar from "../components/shell/TopBar";

function fmtAvg(ms: number | null): string {
  return ms == null ? "—" : `${(ms / 1000).toFixed(1)}s`;
}

export default function Dashboard() {
  const runs = useRuns();

  const stats = useMemo(() => {
    const total = runs.length;
    const done = runs.filter((r) => r.status === "done").length;
    const artifacts = runs.reduce((sum, r) => sum + (r.artifacts || 0), 0);
    const durations = runs.map((r) => r.durationMs).filter((d): d is number => d != null);
    const avg = durations.length
      ? durations.reduce((a, b) => a + b, 0) / durations.length
      : null;
    return {
      total,
      passRate: total ? Math.round((done / total) * 100) : 0,
      artifacts,
      avg,
    };
  }, [runs]);

  return (
    <div className="relative min-h-full">
      {/* Top nav */}
      <TopBar
        showBrand={false}
        left={<span className="text-sm font-semibold text-slate-200">Overview</span>}
        right={
          <>
            <button
              onClick={() => globalThis.dispatchEvent(new Event("sdlc:cmdk"))}
              className="hidden items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-400 transition hover:bg-white/[0.06] hover:text-slate-200 sm:flex"
              title="Open command palette"
            >
              <Search className="h-3.5 w-3.5" />
              Search
              <span className="rounded border border-white/10 px-1.5 py-0.5 font-mono text-[10px]">⌘K</span>
            </button>
            <Link
              to="/app"
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-b from-accent-500 to-accent-600 px-4 py-2 text-sm font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5"
            >
              <Plus className="h-4 w-4" /> New run
            </Link>
          </>
        }
      />

      <main className="mx-auto max-w-[1200px] px-6 py-8">
        {/* Greeting */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-extrabold tracking-tight">
            Welcome back 👋
          </h1>
          <p className="mt-1 text-slate-400">
            Spin up a virtual software team, or revisit a recent run.
          </p>
        </motion.div>

        {/* Stat cards */}
        <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard icon={Activity} label="Total Runs" value={String(stats.total)} hint="all time" delay={0} />
          <StatCard
            icon={CheckCircle2}
            label="Pass Rate"
            value={`${stats.passRate}%`}
            hint="runs completed"
            accent="text-emerald-400"
            delay={0.05}
          />
          <StatCard
            icon={FileCode2}
            label="Artifacts"
            value={String(stats.artifacts)}
            hint="files generated"
            accent="text-accent2-400"
            delay={0.1}
          />
          <StatCard
            icon={Clock}
            label="Avg Duration"
            value={fmtAvg(stats.avg)}
            hint="per run"
            accent="text-amber-400"
            delay={0.15}
          />
        </section>

        {/* Recent runs */}
        <section className="mt-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="label-caps">Recent runs</h2>
            {runs.length > 0 && (
              <Link
                to="/runs"
                className="inline-flex items-center gap-1 text-xs font-semibold text-accent-400 transition hover:text-accent-300"
              >
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>

          {runs.length === 0 ? (
            <EmptyState
              title="No runs yet"
              body="Describe a feature and watch six agents design, build, review, and ship it — live."
              cta={{ to: "/app", label: "Start your first run" }}
            />
          ) : (
            <div className="space-y-3">
              {runs.slice(0, 5).map((run, i) => (
                <RunCard key={run.id} run={run} delay={Math.min(i * 0.04, 0.3)} />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}


