import { useState } from "react";
import { Play, Square, Wand2, GitBranch, Inbox, Loader2 } from "lucide-react";
import { toast } from "../store/toast";
import type { JiraStatus } from "../hooks/useJira";

const SAMPLES = [
  { label: "Login page", value: "Add a login page with email/password to my web app" },
  { label: "Todo API", value: "Add a REST endpoint to create and list todo items" },
  { label: "Contact form", value: "Add a contact form that emails the site owner" },
];

interface Props {
  running: boolean;
  onRun: (request: string, repo?: string) => void;
  onStop: () => void;
  repos?: string[];
  jira?: JiraStatus | null;
}

export default function Composer({ running, onRun, onStop, repos = [], jira }: Readonly<Props>) {
  const [value, setValue] = useState(SAMPLES[0].value);
  const [editRepo, setEditRepo] = useState(false);
  const [repo, setRepo] = useState("");
  const [jiraKey, setJiraKey] = useState("");
  const [importing, setImporting] = useState(false);

  const submit = () => onRun(value, editRepo ? repo : undefined);
  const onKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
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
      setValue(data.request ?? "");
      toast.success(`Imported ${data.issue?.key ?? key} from JIRA`);
    } catch (e) {
      toast.error("Import failed: " + (e as Error).message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <section className="glass rounded-2xl p-4 shadow-soft">
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
          title="Paste an issue key (e.g. PROJ-123) or a JIRA issue URL"
          spellCheck={false}
          className="w-56 rounded-lg border border-white/10 bg-ink-900/60 px-3 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-brand-500 focus:outline-none"
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

      {/* Edit-existing-repo toggle + picker */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
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
            onChange={(e) => setEditRepo(e.target.checked)}
            className="accent-indigo-500"
          />
          <GitBranch className="h-3.5 w-3.5" />
          Edit existing repo
        </label>
        {editRepo && (
          <input
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
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

      <div className="relative">
        <Wand2 className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-brand-400" />
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          disabled={running}
          placeholder="Describe a feature… e.g. Add a login page with email/password"
          className="w-full resize-y rounded-xl border border-white/10 bg-ink-900/60 py-3 pl-10 pr-3 text-sm
            text-slate-100 placeholder:text-slate-500 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:opacity-60"
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {SAMPLES.map((s) => (
            <button
              key={s.label}
              className="chip"
              disabled={running}
              onClick={() => setValue(s.value)}
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
          <button className="btn btn-primary" disabled={running} onClick={submit}>
            <Play className="h-4 w-4" />
            Run team
          </button>
        </div>
      </div>
    </section>
  );
}

