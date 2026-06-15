import { Inbox, Loader2, Play, Square, Wand2, GitBranch } from "lucide-react";
import { useState } from "react";
import { toast } from "../../store/toast";
import type { JiraStatus } from "../../hooks/useJira";

const SAMPLES = [
  {
    label: "Login API",
    title: "Login API with JWT",
    value:
      "Build a login API with JWT auth, refresh token support, role-based access, validation, unit tests, and API docs.",
  },
  {
    label: "Todo API",
    title: "Todo API",
    value: "Create a small REST API to add, list, and delete todo items, with tests.",
  },
  {
    label: "Contact form",
    title: "Contact form",
    value: "Add a contact form that validates input and emails the site owner, with tests.",
  },
  {
    label: "Search + pagination",
    title: "Search with pagination",
    value: "Add a search endpoint with full-text query, filters, and cursor pagination, plus tests.",
  },
];

interface Props {
  running: boolean;
  title: string;
  onTitleChange: (t: string) => void;
  value: string;
  onValueChange: (v: string) => void;
  editRepo: boolean;
  onEditRepoChange: (v: boolean) => void;
  repo: string;
  onRepoChange: (v: string) => void;
  repos: string[];
  jira: JiraStatus | null;
  onRun: () => void;
  onStop: () => void;
}

/**
 * Premium requirement composer (UI_SPEC §5): optional title, multiline
 * requirement, JIRA import, edit-existing-repo picker, quick template chips and
 * a Run Pipeline CTA. Fully controlled so the top bar's Run/Stop can drive it.
 */
export default function RequirementComposer({
  running,
  title,
  onTitleChange,
  value,
  onValueChange,
  editRepo,
  onEditRepoChange,
  repo,
  onRepoChange,
  repos,
  jira,
  onRun,
  onStop,
}: Readonly<Props>) {
  const [jiraKey, setJiraKey] = useState("");
  const [importing, setImporting] = useState(false);

  const onKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") onRun();
  };

  const importFromJira = async () => {
    const key = jiraKey.trim();
    if (!key || importing || running) return;
    setImporting(true);
    try {
      const r = await fetch(`/api/jira/import?key=${encodeURIComponent(key)}`);
      if (!r.ok) {
        const detail = (await r.json().catch(() => ({})))?.detail;
        throw new Error(detail || `HTTP ${r.status}`);
      }
      const data = await r.json();
      onValueChange(data.request ?? "");
      if (data.issue?.summary) onTitleChange(data.issue.summary);
      toast.success(`Imported ${data.issue?.key ?? key} from JIRA`);
    } catch (e) {
      toast.error("Import failed: " + (e as Error).message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <section className="glass rounded-card-lg p-4 shadow-soft">
      {/* Import from JIRA */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="flex items-center gap-1.5 label-caps">
          <Inbox className="h-3.5 w-3.5" /> Import from JIRA
        </span>
        <input
          value={jiraKey}
          onChange={(e) => setJiraKey(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && importFromJira()}
          disabled={running || importing}
          placeholder={jira?.is_mock ? "DEMO-1 or paste a JIRA URL" : "PROJ-123 or paste a JIRA URL"}
          spellCheck={false}
          className="w-52 rounded-lg border border-white/10 bg-ink-900/60 px-3 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-accent-500 focus:outline-none"
        />
        <button
          onClick={importFromJira}
          disabled={running || importing || !jiraKey.trim()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-200 transition hover:bg-white/[0.07] disabled:opacity-50"
        >
          {importing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Inbox className="h-3.5 w-3.5" />}
          Import
        </button>
      </div>

      {/* Title */}
      <input
        value={title}
        onChange={(e) => onTitleChange(e.target.value)}
        disabled={running}
        placeholder="Feature title (optional) — e.g. Login API with JWT"
        className="mb-2.5 w-full rounded-lg border border-white/10 bg-ink-900/60 px-3 py-2 text-sm font-semibold text-slate-100 placeholder:font-normal placeholder:text-slate-500 focus:border-accent-500 focus:outline-none disabled:opacity-60"
      />

      {/* Edit-existing-repo toggle + picker */}
      <div className="mb-2.5 flex flex-wrap items-center gap-2">
        <label
          title="Load an existing repo so the agents edit real code (branch + PR)"
          className={[
            "inline-flex cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition",
            editRepo
              ? "border-indigo-400/40 bg-indigo-400/10 text-indigo-200"
              : "border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.06]",
          ].join(" ")}
        >
          <input
            type="checkbox"
            checked={editRepo}
            disabled={running}
            onChange={(e) => onEditRepoChange(e.target.checked)}
            className="accent-indigo-500"
          />
          <GitBranch className="h-3.5 w-3.5" />
          Edit existing repo
        </label>
        {editRepo && (
          <input
            value={repo}
            onChange={(e) => onRepoChange(e.target.value)}
            list="composer-repo-options"
            disabled={running}
            placeholder="owner/name"
            spellCheck={false}
            className="min-w-[200px] flex-1 rounded-lg border border-white/10 bg-ink-900/60 px-2.5 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
          />
        )}
        <datalist id="composer-repo-options">
          {repos.map((r) => (
            <option key={r} value={r} />
          ))}
        </datalist>
      </div>

      {/* Requirement body */}
      <div className="relative">
        <Wand2 className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-accent-400" />
        <textarea
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          onKeyDown={onKeyDown}
          rows={3}
          disabled={running}
          placeholder={"Describe the feature you want to build…\nTip: one or two sentences is plenty — or pick a sample below to get started."}
          className="w-full resize-y rounded-xl border border-white/10 bg-ink-900/60 py-3 pl-10 pr-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30 disabled:opacity-60"
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {SAMPLES.map((s) => (
            <button
              key={s.label}
              className="chip"
              disabled={running}
              onClick={() => {
                onValueChange(s.value);
                onTitleChange(s.title);
              }}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="mr-1 hidden text-xs text-slate-500 md:inline">⌘/Ctrl + Enter</span>
          <button className="btn btn-ghost" disabled={!running} onClick={onStop}>
            <Square className="h-4 w-4" />
            Stop
          </button>
          <button className="btn btn-primary" disabled={running} onClick={onRun}>
            <Play className="h-4 w-4" />
            Run Pipeline
          </button>
        </div>
      </div>
    </section>
  );
}

