// SDLC Agentic AI — build-free React app (htm + React via ESM CDN).
// No npm install / bundler required: index.html maps "react", "react-dom/client"
// and "htm" to esm.sh, and Tailwind is loaded from its Play CDN.

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import htm from "htm";

const html = htm.bind(React.createElement);
const cx = (...xs) => xs.filter(Boolean).join(" ");

/* ---------------------------------------------------------------- icons */
function IconBase({ size = 16, className = "", strokeWidth = 2, children }) {
  return html`<svg
    width=${size}
    height=${size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth=${strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
    className=${className}
    >${children}</svg
  >`;
}
const Sparkles = (p) =>
  html`<${IconBase} ...${p}
    ><path
      d="M12 3l1.9 4.6L18.5 9.5 13.9 11.4 12 16l-1.9-4.6L5.5 9.5 10.1 7.6 12 3z"
    /><path d="M19 14l.8 2L22 16.8 20 17.6 19.2 20 18.4 17.6 16 16.8 18 16z"
  /><//>`;
const PlayIcon = (p) =>
  html`<${IconBase} ...${p}
    ><polygon points="6 3 20 12 6 21 6 3" fill="currentColor" stroke="none"
  /><//>`;
const StopIcon = (p) =>
  html`<${IconBase} ...${p}
    ><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="none"
  /><//>`;
const Wand = (p) =>
  html`<${IconBase} ...${p}
    ><path d="M15 4V2M15 16v-2M8 9h2M20 9h2M17.8 11.8L19 13M17.8 6.2L19 5M3 21l9-9M12.2 6.2L11 5"
  /><//>`;
const Copy = (p) =>
  html`<${IconBase} ...${p}
    ><rect x="9" y="9" width="13" height="13" rx="2" /><path
      d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
  /><//>`;
const Check = (p) =>
  html`<${IconBase} ...${p}><polyline points="20 6 9 17 4 12" /><//>`;
const DownloadIcon = (p) =>
  html`<${IconBase} ...${p}
    ><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline
      points="7 10 12 15 17 10"
    /><line x1="12" y1="15" x2="12" y2="3"
  /><//>`;
const Rotate = (p) =>
  html`<${IconBase} ...${p}
    ><polyline points="1 4 1 10 7 10" /><path
      d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"
  /><//>`;
const Clock = (p) =>
  html`<${IconBase} ...${p}
    ><circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14"
  /><//>`;
const Workflow = (p) =>
  html`<${IconBase} ...${p}
    ><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect
      x="14"
      y="14"
      width="7"
      height="7"
      rx="1.5"
    /><path d="M10 6.5h4a3 3 0 0 1 3 3V14"
  /><//>`;
const Folder = (p) =>
  html`<${IconBase} ...${p}
    ><path
      d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
  /><//>`;
const Ticket = (p) =>
  html`<${IconBase} ...${p}
    ><path
      d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4z"
    /><path d="M13 6v12"
  /><//>`;
const Inbox = (p) =>
  html`<${IconBase} ...${p}
    ><polyline points="22 12 16 12 14 15 10 15 8 12 2 12" /><path
      d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"
  /><//>`;
const BookOpen = (p) =>
  html`<${IconBase} ...${p}
    ><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path
      d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"
  /><//>`;
const GitHubIcon = (p) =>
  html`<${IconBase} ...${p}
    ><path
      d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"
  /><//>`;
const GitBranch = (p) =>
  html`<${IconBase} ...${p}
    ><line x1="6" y1="3" x2="6" y2="15" /><circle cx="18" cy="6" r="3" /><circle
      cx="6"
      cy="18"
      r="3"
    /><path d="M18 9a9 9 0 0 1-9 9"
  /><//>`;
const Gear = (p) =>
  html`<${IconBase} ...${p}
    ><circle cx="12" cy="12" r="3" /><path
      d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
  /><//>`;
const ChevronDown = (p) =>
  html`<${IconBase} ...${p}><polyline points="6 9 12 15 18 9" /><//>`;

const Spinner = ({ className = "" }) =>
  html`<span
    className=${cx(
      "inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent",
      className
    )}
  ></span>`;

const FILE_EMOJI = { code: "📄", test: "🧪", config: "⚙️", doc: "📘", markdown: "📝" };
const fileGlyph = (t) => FILE_EMOJI[t] || "📃";

/* --------------------------------------------------------- stream hook */
const INITIAL = {
  runStatus: "idle",
  agentOrder: [],
  agents: {},
  artifactOrder: [],
  artifacts: {},
  loops: [],
  grounding: null,
  repoContext: null,
  request: "",
  durationMs: null,
  providerLabel: null,
  error: null,
};

function useAgentStream() {
  const [config, setConfig] = useState(null);
  const [state, setState] = useState(INITIAL);
  const esRef = useRef(null);
  const finishedRef = useRef(false);

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => setConfig(null));
  }, []);

  const closeStream = useCallback(() => {
    if (esRef.current) esRef.current.close();
    esRef.current = null;
  }, []);

  const apply = useCallback((ev) => {
    setState((s) => {
      switch (ev.type) {
        case "run_start":
          return { ...s, providerLabel: ev.provider_label, request: ev.request || "" };
        case "plan": {
          const agents = {};
          const agentOrder = [];
          for (const step of ev.steps) {
            agentOrder.push(step.id);
            agents[step.id] = {
              ...step,
              status: "queued",
              stream: "",
              summary: "",
              iteration: 0,
              verdict: null,
              comments: [],
            };
          }
          return { ...s, agents, agentOrder };
        }
        case "grounding":
          return {
            ...s,
            grounding: {
              provider: ev.provider,
              label: ev.label,
              count: ev.count,
              citations: ev.citations || [],
              subqueries: ev.subqueries || [],
              error: ev.error || null,
            },
          };
        case "repo_context":
          return {
            ...s,
            repoContext: {
              repo: ev.repo,
              count: ev.count,
              files: ev.files || [],
              error: ev.error || null,
            },
          };
        case "agent_start": {
          const prev = s.agents[ev.agent];
          if (!prev) return s;
          return {
            ...s,
            agents: {
              ...s.agents,
              [ev.agent]: {
                ...prev,
                status: "working",
                stream: "",
                summary: "",
                iteration: ev.iteration,
                verdict: null,
              },
            },
          };
        }
        case "delta": {
          const prev = s.agents[ev.agent];
          if (!prev) return s;
          return {
            ...s,
            agents: { ...s.agents, [ev.agent]: { ...prev, stream: prev.stream + ev.text } },
          };
        }
        case "artifact": {
          const a = ev.artifact;
          const exists = !!s.artifacts[a.name];
          return {
            ...s,
            artifactOrder: exists ? s.artifactOrder : [...s.artifactOrder, a.name],
            artifacts: { ...s.artifacts, [a.name]: a },
          };
        }
        case "agent_done": {
          const prev = s.agents[ev.agent];
          if (!prev) return s;
          let status = "done";
          if (ev.verdict === "approve") status = "approved";
          else if (ev.verdict === "request_changes") status = "changes";
          return {
            ...s,
            agents: {
              ...s.agents,
              [ev.agent]: {
                ...prev,
                status,
                summary: ev.summary,
                verdict: ev.verdict,
                comments: ev.comments || [],
              },
            },
          };
        }
        case "loop":
          return { ...s, loops: [...s.loops, { iteration: ev.iteration, comments: ev.comments }] };
        case "run_complete":
          finishedRef.current = true;
          return { ...s, runStatus: "done", durationMs: ev.duration_ms };
        case "error":
          return { ...s, error: ev.message };
        default:
          return s;
      }
    });
  }, []);

  const run = useCallback(
    (request, repo) => {
      const trimmed = (request || "").trim();
      if (!trimmed) return;
      closeStream();
      finishedRef.current = false;
      setState({ ...INITIAL, runStatus: "running" });
      const qs = new URLSearchParams({ request: trimmed });
      if (repo && repo.includes("/")) qs.set("repo", repo.trim());
      const es = new EventSource(`/api/stream?${qs.toString()}`);
      esRef.current = es;
      es.onmessage = (e) => {
        try {
          apply(JSON.parse(e.data));
        } catch (_) {}
      };
      es.onerror = () => {
        if (finishedRef.current) {
          closeStream();
          return;
        }
        closeStream();
        setState((s) => ({
          ...s,
          runStatus: s.runStatus === "running" ? "error" : s.runStatus,
          error: s.error || "Connection closed unexpectedly.",
        }));
      };
    },
    [apply, closeStream]
  );

  const stop = useCallback(() => {
    closeStream();
    setState((s) => ({ ...s, runStatus: s.runStatus === "running" ? "stopped" : s.runStatus }));
  }, [closeStream]);

  useEffect(() => () => closeStream(), [closeStream]);

  return { config, run, stop, ...state };
}

/* ------------------------------------------------------------- Header */
function Header({ config, providerLabel, runStatus, durationMs, jira, github, admin }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const isMock = config ? config.is_mock : true;
  const label = providerLabel || (config && config.provider_label) || "…";
  const dot =
    runStatus === "running"
      ? "animate-pulse bg-brand-400"
      : runStatus === "done"
      ? "bg-emerald-400"
      : runStatus === "error"
      ? "bg-rose-400"
      : "bg-slate-600";
  return html`<header
    className="sticky top-0 z-20 border-b border-white/10 bg-ink-950/70 backdrop-blur-xl"
  >
    <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-6 py-3.5">
      <div className="flex items-center gap-3">
        <div
          className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-600 text-xl shadow-glow animate-floaty"
        >
          🧩
        </div>
        <div>
          <h1 className="text-[17px] font-extrabold leading-tight tracking-tight">
            SDLC Agentic AI
          </h1>
          <p className="text-xs text-slate-400">
            A virtual software team — requirements → design → code → tests → review → docs
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2.5">
        ${durationMs != null &&
        html`<span
          className="hidden items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 sm:flex"
        >
          <${Clock} size=${14} /> ${(durationMs / 1000).toFixed(1)}s
        </span>`}
        ${jira &&
        html`<span
          title=${jira.is_mock
            ? "JIRA mock — no account, nothing leaves your machine."
            : `Connected to ${jira.host} (project ${jira.project_key})`}
          className=${cx(
            "hidden items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold sm:flex",
            jira.is_mock
              ? "border-amber-400/40 bg-amber-400/10 text-amber-300"
              : "border-sky-400/40 bg-sky-400/10 text-sky-300"
          )}
        >
          <${Ticket} size=${14} /> JIRA: ${jira.is_mock ? "Mock (free)" : jira.host}
        </span>`}
        ${github &&
        html`<span
          title=${github.is_mock
            ? "GitHub mock — no account, nothing leaves your machine."
            : `Publishes to ${github.repo}`}
          className=${cx(
            "hidden items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold sm:flex",
            github.is_mock
              ? "border-amber-400/40 bg-amber-400/10 text-amber-300"
              : "border-indigo-400/40 bg-indigo-400/10 text-indigo-300"
          )}
        >
          <${GitHubIcon} size=${14} /> GitHub: ${github.is_mock ? "Mock (free)" : github.repo}
        </span>`}
        <span
          title=${isMock
            ? "Running on the free mock provider — no tokens spent."
            : "Running on a live LLM provider."}
          className=${cx(
            "flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold",
            isMock
              ? "border-amber-400/40 bg-amber-400/10 text-amber-300"
              : "border-emerald-400/40 bg-emerald-400/10 text-emerald-300"
          )}
        >
          <${Sparkles} size=${14} /> ${label}
        </span>
        <span className=${cx("h-2.5 w-2.5 rounded-full", dot)}></span>
        ${admin &&
        html`<div className="relative">
          <button
            onClick=${() => setSettingsOpen((v) => !v)}
            title="Switch providers (mock / live)"
            className=${cx(
              "grid h-8 w-8 place-items-center rounded-lg border transition",
              settingsOpen
                ? "border-brand-500/50 bg-brand-500/15 text-brand-300"
                : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
            )}
          >
            <${Gear} size=${15} />
          </button>
          ${settingsOpen &&
          html`<${SettingsPanel} admin=${admin} onClose=${() => setSettingsOpen(false)} />`}
        </div>`}
      </div>
    </div>
  </header>`;
}

/* ----------------------------------------------------------- Composer */
const SAMPLES = [
  { label: "Login page", value: "Add a login page with email/password to my web app" },
  { label: "Todo API", value: "Add a REST endpoint to create and list todo items" },
  { label: "Contact form", value: "Add a contact form that emails the site owner" },
];

function Composer({ running, onRun, onStop, jira, repos, notify }) {
  const [value, setValue] = useState(SAMPLES[0].value);
  const [jiraKey, setJiraKey] = useState("");
  const [importing, setImporting] = useState(false);
  const [editRepo, setEditRepo] = useState(false);
  const [repo, setRepo] = useState("");
  const submit = () => onRun(value, editRepo ? repo : "");
  const onKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
  };

  const importFromJira = async () => {
    const key = jiraKey.trim();
    if (!key || importing) return;
    setImporting(true);
    try {
      const r = await fetch(`/api/jira/import?key=${encodeURIComponent(key)}`);
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      const data = await r.json();
      setValue(data.request || "");
      notify && notify(`Imported ${data.issue?.key || key} from JIRA`);
    } catch (e) {
      notify && notify("Import failed: " + e.message);
    } finally {
      setImporting(false);
    }
  };

  return html`<section
    className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-soft backdrop-blur-xl"
  >
    <div className="mb-3 flex flex-wrap items-center gap-2">
      <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
        <${Inbox} size=${14} /> Import from JIRA
      </span>
      <input
        value=${jiraKey}
        onChange=${(e) => setJiraKey(e.target.value)}
        onKeyDown=${(e) => e.key === "Enter" && importFromJira()}
        disabled=${running || importing}
        placeholder=${jira && jira.is_mock ? "DEMO-1 or paste a JIRA URL" : "PROJ-123 or paste a JIRA URL"}
        title="Paste an issue key (e.g. PROJ-123) or a JIRA issue URL"
        className="w-56 rounded-lg border border-white/10 bg-ink-900/60 px-3 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-brand-500 focus:outline-none"
      />
      <button
        onClick=${importFromJira}
        disabled=${running || importing || !jiraKey.trim()}
        className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-200 transition hover:bg-white/[0.07] disabled:opacity-50"
      >
        ${importing ? html`<${Spinner} />` : html`<${Inbox} size=${13} />`} Import
      </button>
    </div>

    <div className="mb-3 flex flex-wrap items-center gap-2">
      <label
        className=${cx(
          "inline-flex cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition",
          editRepo
            ? "border-indigo-400/40 bg-indigo-400/10 text-indigo-200"
            : "border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.06]"
        )}
        title="Load an existing repo so the agents edit real code (branch + PR)"
      >
        <input
          type="checkbox"
          checked=${editRepo}
          disabled=${running}
          onChange=${(e) => setEditRepo(e.target.checked)}
          className="accent-indigo-500"
        />
        <${GitBranch} size=${13} /> Edit existing repo
      </label>
      ${editRepo &&
      html`<input
        value=${repo}
        onInput=${(e) => setRepo(e.target.value)}
        list="composer-repo-options"
        disabled=${running}
        placeholder="owner/name"
        spellcheck=${false}
        className="min-w-[200px] flex-1 rounded-lg border border-white/10 bg-ink-900/60 px-2.5 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
      />`}
      <datalist id="composer-repo-options">
        ${(repos || []).map((r) => html`<option key=${r} value=${r}></option>`)}
      </datalist>
    </div>

    <div className="relative">
      <span className="pointer-events-none absolute left-3.5 top-3 text-brand-400">
        <${Wand} size=${16} />
      </span>
      <textarea
        value=${value}
        onChange=${(e) => setValue(e.target.value)}
        onKeyDown=${onKeyDown}
        rows=${2}
        disabled=${running}
        placeholder="Describe a feature… e.g. Add a login page with email/password"
        className="w-full resize-y rounded-xl border border-white/10 bg-ink-900/60 py-3 pl-10 pr-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:opacity-60"
      ></textarea>
    </div>
    <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap items-center gap-2">
        ${SAMPLES.map(
          (s) => html`<button
            key=${s.label}
            disabled=${running}
            onClick=${() => setValue(s.value)}
            className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 transition-colors hover:border-brand-500/60 hover:text-white disabled:opacity-50"
          >
            ${s.label}
          </button>`
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="mr-1 hidden text-xs text-slate-500 md:inline">⌘/Ctrl + Enter</span>
        <button
          onClick=${onStop}
          disabled=${!running}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm font-semibold text-slate-200 transition hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-50"
        >
          <${StopIcon} size=${15} /> Stop
        </button>
        <button
          onClick=${submit}
          disabled=${running}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-b from-brand-500 to-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 hover:shadow-glow disabled:cursor-not-allowed disabled:opacity-50"
        >
          <${PlayIcon} size=${15} /> Run team
        </button>
      </div>
    </div>
  </section>`;
}

/* ---------------------------------------------------------- AgentCard */
const STATUS = {
  queued: { label: "queued", cls: "text-slate-400 border-white/10", spin: false },
  working: { label: "working", cls: "text-brand-300 border-brand-500/50", spin: true },
  done: { label: "done", cls: "text-emerald-300 border-emerald-400/40", spin: false },
  approved: { label: "approved", cls: "text-emerald-300 border-emerald-400/40", spin: false },
  changes: { label: "changes requested", cls: "text-amber-300 border-amber-400/40", spin: false },
  error: { label: "error", cls: "text-rose-300 border-rose-400/40", spin: false },
};

function AgentCard({ agent }) {
  const meta = STATUS[agent.status] || STATUS.queued;
  const working = agent.status === "working";
  const dim = agent.status === "queued";
  return html`<div
    className=${cx(
      "sdlc-enter rounded-2xl border bg-white/[0.04] p-4 backdrop-blur-xl transition-all duration-300",
      working ? "border-brand-500/50 shadow-glow" : "border-white/10 shadow-soft",
      dim ? "opacity-60" : "opacity-100"
    )}
  >
    <div className="flex items-center gap-3">
      <div
        className=${cx(
          "grid h-11 w-11 shrink-0 place-items-center rounded-xl border text-xl",
          working ? "border-brand-500/60 bg-brand-500/15 animate-pulse-ring" : "border-white/10 bg-white/[0.04]"
        )}
      >
        ${agent.emoji}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h3 className="truncate font-semibold text-slate-100">${agent.name}</h3>
          ${agent.iteration > 0 &&
          html`<span
            className="rounded-full border border-brand-500/40 bg-brand-500/15 px-2 py-0.5 text-[10px] font-semibold text-brand-300"
            >revision ${agent.iteration}</span
          >`}
        </div>
        <p className="truncate text-xs text-slate-400">${agent.role}</p>
      </div>
      <span
        className=${cx(
          "flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold",
          meta.cls
        )}
      >
        ${meta.spin ? html`<${Spinner} />` : null} ${meta.label}
      </span>
    </div>

    ${(working || agent.stream) &&
    html`<div
      className=${cx(
        "mt-3 max-h-56 overflow-auto whitespace-pre-wrap rounded-xl border border-white/5 bg-ink-950/50 p-3 text-[13px] leading-relaxed text-slate-300",
        working ? "sdlc-cursor" : ""
      )}
    >
      ${agent.stream}
    </div>`}

    ${agent.summary &&
    html`<p className="mt-2.5 flex items-start gap-1.5 text-xs text-emerald-300/90">
      <span className="mt-0.5"><${Check} size=${13} /></span><span>${agent.summary}</span>
    </p>`}
  </div>`;
}

/* ------------------------------------------------------------ Pipeline */
function Pipeline({ agentOrder, agents, loops }) {
  if (agentOrder.length === 0) {
    return html`<div
      className="grid place-items-center rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center shadow-soft backdrop-blur-xl"
    >
      <div className="mb-3 text-slate-500"><${Workflow} size=${36} /></div>
      <p className="text-sm text-slate-400">
        Describe a feature above and hit
        <span className="text-slate-200"> Run team </span>to watch the agents collaborate live.
      </p>
    </div>`;
  }
  return html`<div className="space-y-3">
    ${agentOrder.map((id, i) => {
      const agent = agents[id];
      if (!agent) return null;
      const showLoops = id === "reviewer" && loops.length > 0;
      return html`<div key=${id} className="space-y-3">
        ${i > 0 &&
        html`<div className="ml-[26px] h-3 w-px bg-gradient-to-b from-white/15 to-transparent"></div>`}
        <${AgentCard} agent=${agent} />
        ${showLoops &&
        loops.map(
          (loop) => html`<div
            key=${"loop-" + loop.iteration}
            className="sdlc-fade flex items-start gap-2.5 rounded-xl border border-dashed border-amber-400/40 bg-amber-400/[0.06] p-3 text-amber-200"
          >
            <span className="mt-0.5"><${Rotate} size=${15} /></span>
            <div className="text-xs">
              <p className="font-semibold">
                Reviewer requested changes — looping back to the Developer (revision
                ${" "}${loop.iteration}).
              </p>
              ${loop.comments &&
              loop.comments.length > 0 &&
              html`<ul className="mt-1 list-disc space-y-0.5 pl-4 text-amber-200/80">
                ${loop.comments.map((c, idx) => html`<li key=${idx}>${c}</li>`)}
              </ul>`}
            </div>
          </div>`
        )}
      </div>`;
    })}
  </div>`;
}

/* ----------------------------------------------------------- CodeBlock */
// NOTE: highlighting tokenizes first, then wraps each token EXACTLY ONCE.
// We must never run another regex over already-injected <span> markup, or the
// number/attribute regexes would match digits inside Tailwind class names
// (e.g. the "300" in text-violet-300) and corrupt the HTML — which previously
// leaked stray text like `300">` into the rendered code.
const KEYWORD_SET = new Set(
  (
    "def class return import from as if elif else for while try except finally raise " +
    "with async await lambda yield pass break continue in is not and or None True False " +
    "self const let var function export default new typeof interface type extends " +
    "implements public private void null undefined this"
  ).split(" ")
);
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const wrap = (cls, t) => `<span class="${cls}">${esc(t)}</span>`;

function _nextIsParen(parts, i) {
  for (let j = i + 1; j < parts.length; j++) {
    if (/^\s+$/.test(parts[j])) continue;
    return parts[j][0] === "(";
  }
  return false;
}

/** Highlight a fragment of code that contains NO markup (wrap once per token). */
function hlCode(frag) {
  const parts = frag.match(/[A-Za-z_$][\w$]*|\d[\w.]*|\s+|[^\sA-Za-z0-9_$]+/g) || [];
  let out = "";
  for (let i = 0; i < parts.length; i++) {
    const t = parts[i];
    if (/^[A-Za-z_$]/.test(t)) {
      if (KEYWORD_SET.has(t)) out += wrap("text-violet-300", t);
      else if (_nextIsParen(parts, i)) out += wrap("text-sky-300", t);
      else out += esc(t);
    } else if (/^\d/.test(t)) {
      out += wrap("text-amber-300", t);
    } else {
      out += esc(t); // whitespace or symbols
    }
  }
  return out;
}

/** Highlight a single raw HTML tag ("<...>"), escaping each piece once. */
function hlTag(tag) {
  const parts = tag.match(/<\/?|\/?>|"[^"]*"|'[^']*'|[A-Za-z_:][\w:.-]*|\s+|[^\s]/g) || [];
  let out = "";
  let sawAngle = false;
  let named = false;
  for (const t of parts) {
    if (t === "<" || t === "</") {
      out += wrap("text-slate-500", t);
      sawAngle = true;
      named = false;
    } else if (t === ">" || t === "/>") {
      out += wrap("text-slate-500", t);
      sawAngle = false;
    } else if (/^["']/.test(t)) {
      out += wrap("text-emerald-300", t);
    } else if (/^[A-Za-z_:]/.test(t)) {
      if (sawAngle && !named) {
        out += wrap("text-rose-300", t); // tag name
        named = true;
      } else {
        out += wrap("text-amber-200", t); // attribute name
      }
    } else {
      out += esc(t);
    }
  }
  return out;
}

function hlMarkup(line) {
  let out = "";
  let last = 0;
  let m;
  const re = /<[^>]*>/g;
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) out += esc(line.slice(last, m.index)); // text node
    out += hlTag(m[0]);
    last = m.index + m[0].length;
  }
  if (last < line.length) out += esc(line.slice(last));
  return out;
}

function highlight(line, lang) {
  if (lang === "markdown") {
    if (/^#{1,6}\s/.test(line)) return wrap("text-brand-300 font-semibold", line);
    const b = line.match(/^(\s*[-*]\s)(.*)$/);
    if (b) return wrap("text-violet-300", b[1]) + esc(b[2]);
    return esc(line);
  }
  const hash = (lang === "python" || lang === "yaml") && line.match(/^(\s*)(#.*)$/);
  if (hash) return esc(hash[1]) + wrap("text-slate-500 italic", hash[2]);
  if (lang === "html" || lang === "markup") return hlMarkup(line);

  // Generic code: split out string literals, highlight the rest as code.
  const re = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g;
  let out = "";
  let last = 0;
  let m;
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) out += hlCode(line.slice(last, m.index));
    out += wrap("text-emerald-300", m[0]); // string literal
    last = m.index + m[0].length;
  }
  if (last < line.length) out += hlCode(line.slice(last));
  return out;
}

function CodeBlock({ content, language }) {
  const lines = useMemo(() => content.replace(/\n$/, "").split("\n"), [content]);
  const prose = language === "markdown" || language === "text";
  return html`<div className="h-full overflow-auto p-4 font-mono text-[12.5px] leading-[1.6]">
    <table className="w-full border-collapse">
      <tbody>
        ${lines.map(
          (line, i) => html`<tr key=${i} className="align-top">
            ${!prose &&
            html`<td className="w-8 select-none pr-4 text-right text-slate-600">${i + 1}</td>`}
            <td
              className="whitespace-pre-wrap break-words text-slate-200"
              dangerouslySetInnerHTML=${{ __html: highlight(line, language) || "&nbsp;" }}
            ></td>
          </tr>`
        )}
      </tbody>
    </table>
  </div>`;
}

/* -------------------------------------------------------- ArtifactPanel */
function ArtifactPanel({ artifactOrder, artifacts, notify }) {
  const [selected, setSelected] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!selected && artifactOrder.length > 0) setSelected(artifactOrder[0]);
    if (selected && !artifacts[selected] && artifactOrder.length > 0) setSelected(artifactOrder[0]);
  }, [artifactOrder, artifacts, selected]);

  const active = selected ? artifacts[selected] : undefined;
  const count = artifactOrder.length;

  const copy = () => {
    if (!active) return;
    navigator.clipboard.writeText(active.content).then(() => {
      setCopied(true);
      notify && notify("Copied to clipboard");
      setTimeout(() => setCopied(false), 1400);
    });
  };
  const download = () => {
    if (!active) return;
    const blob = new Blob([active.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = active.name.split("/").pop() || "artifact.txt";
    a.click();
    URL.revokeObjectURL(url);
    notify && notify("Downloaded " + a.download);
  };

  return html`<aside
    className="flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] shadow-soft backdrop-blur-xl"
  >
    <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
      <div className="flex items-center gap-2 text-slate-300">
        <${Folder} size=${15} />
        <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
          Artifacts
        </span>
      </div>
      <span
        className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-0.5 text-xs text-slate-300"
        >${count} file${count === 1 ? "" : "s"}</span
      >
    </div>

    ${count === 0
      ? html`<div className="grid flex-1 place-items-center p-10 text-center">
          <p className="text-sm text-slate-500">
            Generated files (specs, code, tests, docs) will appear here as the team works.
          </p>
        </div>`
      : html`<${React.Fragment}>
          <ul className="max-h-44 overflow-auto border-b border-white/10 p-2">
            ${artifactOrder.map((name) => {
              const a = artifacts[name];
              const isActive = name === selected;
              return html`<li key=${name}>
                <button
                  onClick=${() => setSelected(name)}
                  className=${cx(
                    "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm transition-colors",
                    isActive
                      ? "bg-brand-500/15 text-white ring-1 ring-brand-500/40"
                      : "text-slate-300 hover:bg-white/[0.05]"
                  )}
                >
                  <span>${fileGlyph(a.type)}</span>
                  <span className="truncate font-mono text-[12.5px]">${name}</span>
                  <span
                    className="ml-auto rounded border border-white/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-500"
                    >${a.type}</span
                  >
                </button>
              </li>`;
            })}
          </ul>

          <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
            <span className="truncate font-mono text-xs text-slate-400">
              ${active ? `${active.name} · ${active.language}` : "Select a file"}
            </span>
            <div className="flex items-center gap-1.5">
              <button
                onClick=${copy}
                disabled=${!active}
                className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-xs text-slate-200 transition hover:bg-white/[0.07] disabled:opacity-50"
              >
                ${copied ? html`<${Check} size=${14} />` : html`<${Copy} size=${14} />`}
                ${copied ? "Copied" : "Copy"}
              </button>
              <button
                onClick=${download}
                disabled=${!active}
                className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-xs text-slate-200 transition hover:bg-white/[0.07] disabled:opacity-50"
              >
                <${DownloadIcon} size=${14} /> Save
              </button>
            </div>
          </div>

          <div className="min-h-[240px] flex-1 overflow-hidden bg-ink-950/40">
            ${active && html`<${CodeBlock} content=${active.content} language=${active.language} />`}
          </div>
        <//>`}
  </aside>`;
}

/* ----------------------------------------------------------------- App */
function statusText(runStatus, durationMs) {
  if (runStatus === "idle") return "idle";
  if (runStatus === "running") return "running…";
  if (runStatus === "done")
    return "done" + (durationMs != null ? ` in ${(durationMs / 1000).toFixed(1)}s` : "");
  return runStatus;
}

/* ------------------------------------------------------------- useJira */
function useJira(notify) {
  const [status, setStatus] = useState(null);
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState(null); // {epic, created:[...]}

  const refresh = useCallback(() => {
    fetch("/api/jira/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const reset = useCallback(() => setCreated(null), []);

  const createStories = useCallback(
    async (bundle) => {
      if (creating || !bundle || !(bundle.stories || []).length) return;
      // Confirm before writing to a REAL board.
      if (status && !status.is_mock) {
        const ok = window.confirm(
          `Create ${bundle.stories.length} stories in JIRA (${status.host} / ${status.project_key})?`
        );
        if (!ok) return;
      }
      setCreating(true);
      try {
        const r = await fetch("/api/jira/create-stories", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            stories: bundle.stories,
            epic: bundle.epic || null,
            create_epic: !!bundle.epic,
          }),
        });
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
        const data = await r.json();
        setCreated(data);
        notify && notify(`Created ${data.count} issue(s) in JIRA`);
      } catch (e) {
        notify && notify("JIRA create failed: " + e.message);
      } finally {
        setCreating(false);
      }
    },
    [creating, status, notify]
  );

  return { status, creating, created, createStories, reset, refresh };
}

/* ----------------------------------------------------------- useGitHub */
function useGitHub(notify) {
  const [status, setStatus] = useState(null);
  const [repos, setRepos] = useState([]);
  const [publishing, setPublishing] = useState(false);
  const [result, setResult] = useState(null); // PublishResult

  const refresh = useCallback(() => {
    fetch("/api/github/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus(null));
    fetch("/api/github/repos")
      .then((r) => r.json())
      .then((d) => setRepos(d.repos || []))
      .catch(() => setRepos([]));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const reset = useCallback(() => setResult(null), []);

  const publish = useCallback(
    async (files, title, opts = {}) => {
      const list = Array.isArray(files) ? files : Object.values(files || {});
      if (publishing || !list.length) return;
      const repo = (opts.repo || "").trim();
      const createNew = !!opts.createNew;
      // Confirm before writing to a REAL repo.
      if (status && !status.is_mock) {
        let action;
        if (createNew) {
          action = repo.includes("/")
            ? `create new repo ${repo} and push`
            : `create a new repo under ${status.owner || "your account"} and push`;
        } else {
          action = `open a PR against ${repo}`;
        }
        if (!window.confirm(`Publish ${list.length} file(s) to GitHub — ${action}?`)) return;
      }
      setPublishing(true);
      try {
        const r = await fetch("/api/github/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: (title || "SDLC feature").slice(0, 120),
            request: title || "",            // original feature → better AI commit msg
            repo: repo || null,              // empty + owner-only → backend auto-names a new repo
            create_new: createNew,
            artifacts: list.map((a) => ({ name: a.name, content: a.content })),
          }),
        });
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
        const data = await r.json();
        setResult(data);
        notify && notify(data.mode === "new_repo" ? `Created ${data.repo} & pushed` : `Opened PR #${data.pull_request?.number}`);
      } catch (e) {
        notify && notify("GitHub publish failed: " + e.message);
      } finally {
        setPublishing(false);
      }
    },
    [publishing, status, notify]
  );

  return { status, repos, publishing, result, publish, reset, refresh };
}

/* ------------------------------------------------------------ useAdmin */
function useAdmin(notify) {
  const [state, setState] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    fetch("/api/admin/providers")
      .then((r) => r.json())
      .then(setState)
      .catch(() => setState(null));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const setProvider = useCallback(
    async (key, value) => {
      if (busy) return;
      setBusy(true);
      try {
        const r = await fetch("/api/admin/providers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [key]: value }),
        });
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
        setState(await r.json());
        notify && notify(`Switched ${key.replace("_provider", "")} → ${value}`);
      } catch (e) {
        notify && notify("Switch failed: " + e.message);
      } finally {
        setBusy(false);
      }
    },
    [busy, notify]
  );

  const reset = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await fetch("/api/admin/providers/reset", { method: "POST" });
      setState(await r.json());
      notify && notify("Reverted to .env defaults");
    } catch (e) {
      notify && notify("Reset failed: " + e.message);
    } finally {
      setBusy(false);
    }
  }, [busy, notify]);

  return { state, busy, setProvider, setReset: reset, refresh };
}

/* -------------------------------------------------------- SettingsPanel */
const PROVIDER_META = {
  llm: { label: "LLM", live: "azure", icon: Sparkles },
  knowledge: { label: "Foundry IQ", live: "foundry", icon: BookOpen },
  jira: { label: "JIRA", live: "cloud", icon: Ticket },
  github: { label: "GitHub", live: "cloud", icon: GitHubIcon },
};

function SettingsPanel({ admin, onClose }) {
  const providers = admin.state ? admin.state.providers : null;
  return html`<div
    className="absolute right-0 top-12 z-30 w-[340px] rounded-2xl border border-white/10 bg-ink-900/95 p-3 shadow-soft backdrop-blur-xl sdlc-fade"
  >
    <div className="mb-2 flex items-center justify-between px-1">
      <p className="text-sm font-semibold text-slate-100">Providers — mock / live</p>
      <button
        onClick=${onClose}
        className="rounded-md px-1.5 text-slate-400 hover:text-slate-200"
        title="Close"
      >
        ✕
      </button>
    </div>
    <p className="mb-2 px-1 text-[11px] leading-relaxed text-slate-400">
      Switch any integration without a restart. Choices persist (runtime-config). Live
      falls back to mock if not configured.
    </p>
    ${!providers
      ? html`<p className="px-1 py-3 text-xs text-slate-500">Loading…</p>`
      : Object.entries(PROVIDER_META).map(([key, meta]) => {
          const p = providers[key];
          if (!p) return null;
          const isLive = p.selected !== "mock";
          const fellBack = isLive && p.effective === "mock";
          return html`<div
            key=${key}
            className="mb-1.5 flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <span className="text-slate-300"><${meta.icon} size=${15} /></span>
              <div>
                <p className="text-xs font-semibold text-slate-200">${meta.label}</p>
                <p className="text-[10px] text-slate-500">
                  ${p.selected}${fellBack ? " → mock (not configured)" : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-ink-950/60 p-0.5">
              <button
                disabled=${admin.busy}
                onClick=${() => admin.setProvider(`${key}_provider`, "mock")}
                className=${cx(
                  "rounded-md px-2 py-1 text-[11px] font-semibold transition",
                  !isLive ? "bg-amber-400/20 text-amber-200" : "text-slate-400 hover:text-slate-200"
                )}
              >
                Mock
              </button>
              <button
                disabled=${admin.busy}
                onClick=${() => admin.setProvider(`${key}_provider`, meta.live)}
                className=${cx(
                  "rounded-md px-2 py-1 text-[11px] font-semibold transition",
                  isLive ? "bg-emerald-400/20 text-emerald-200" : "text-slate-400 hover:text-slate-200"
                )}
              >
                Live
              </button>
            </div>
          </div>`;
        })}
    <button
      onClick=${admin.setReset}
      disabled=${admin.busy}
      className="mt-1 w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/[0.07] disabled:opacity-50"
    >
      Reset to .env defaults
    </button>
  </div>`;
}

/* ------------------------------------------------------ GitHubPublish */
function GitHubPublish({ artifacts, title, github, repos, editRepo, publishing, result, onPublish }) {
  const all = Object.values(artifacts || {}).filter(
    (a) => a.name !== "stories.json" && (a.content || "").trim()
  );
  const [deselected, setDeselected] = useState({}); // name -> true = excluded
  const [repo, setRepo] = useState("");
  const [createNew, setCreateNew] = useState(false);
  const [showFiles, setShowFiles] = useState(false);

  // Owner-only mode: a GitHub owner is set but no default repo → default to
  // creating a new repo (the agent auto-names it from the feature).
  const ownerOnly = !!(github && github.has_default_repo === false && !github.is_mock);

  // Seed the repo field: prefer the repo whose code we just edited, else the
  // configured default repo. In owner-only mode leave it blank (auto-named).
  useEffect(() => {
    const seed = editRepo || (github && github.has_default_repo ? github.repo : "");
    if (seed) setRepo((r) => r || seed);
  }, [github, editRepo]);

  // Default the create-new toggle on when there's no default repo to PR against.
  useEffect(() => {
    if (ownerOnly && !editRepo) setCreateNew(true);
  }, [ownerOnly, editRepo]);

  if (!all.length) return null;
  const isMock = github ? github.is_mock : true;
  const chosen = all.filter((a) => !deselected[a.name]);
  const toggle = (name) => setDeselected((d) => ({ ...d, [name]: !d[name] }));
  // owner/name → ok; owner-only create-new allows a blank or name-only repo.
  const repoOk = repo.includes("/") || (ownerOnly && createNew);
  const canPublish = !publishing && chosen.length > 0 && repoOk;
  const ownerLabel = github && github.owner ? github.owner : "your account";

  return html`<div
    className="sdlc-fade rounded-2xl border border-indigo-400/30 bg-indigo-400/[0.06] p-4 shadow-soft"
  >
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2.5">
        <div className="grid h-9 w-9 place-items-center rounded-lg border border-indigo-400/40 bg-indigo-400/15 text-indigo-300">
          <${GitHubIcon} size=${16} />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-100">
            Publish to GitHub
            <span className="text-slate-400"> · ${chosen.length} of ${all.length} file${all.length === 1 ? "" : "s"}</span>
          </p>
          <p className="text-xs text-slate-400">
            ${isMock
              ? "GitHub mock — no account; simulates the chosen action offline."
              : createNew
              ? (repo.includes("/")
                  ? `Creates new repo ${repo} and pushes the selected files.`
                  : `Creates a new repo under ${ownerLabel} (auto-named) and pushes the selected files.`)
              : "Opens a branch + PR with the selected files."}
          </p>
        </div>
      </div>
      <button
        onClick=${() => onPublish(chosen, title, { repo, createNew })}
        disabled=${!canPublish}
        title=${canPublish ? "" : (ownerOnly ? "Tick 'Create new repository' or enter owner/name" : "Enter a repo as owner/name")}
        className=${cx(
          "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-semibold transition",
          "border border-indigo-400/40 bg-indigo-400/15 text-indigo-200 hover:bg-indigo-400/25 disabled:opacity-50"
        )}
      >
        ${publishing ? html`<${Spinner} />` : html`<${GitBranch} size=${15} />`}
        ${publishing ? "Publishing…" : createNew ? "Create repo & push" : "Open PR"}
      </button>
    </div>

    <!-- Repo picker + create-new -->
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <label className="text-[11px] uppercase tracking-wide text-slate-500">Repo</label>
      <input
        value=${repo}
        onInput=${(e) => setRepo(e.target.value)}
        list="gh-repo-options"
        placeholder=${ownerOnly ? "blank = auto-named, or name / owner/name" : "owner/name"}
        spellcheck=${false}
        className="min-w-[220px] flex-1 rounded-lg border border-white/10 bg-ink-900/60 px-2.5 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
      />
      <datalist id="gh-repo-options">
        ${(repos || []).map((r) => html`<option key=${r} value=${r}></option>`)}
      </datalist>
      <label
        className=${cx(
          "inline-flex cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs transition",
          createNew
            ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-200"
            : "border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.06]"
        )}
      >
        <input
          type="checkbox"
          checked=${createNew}
          onChange=${(e) => setCreateNew(e.target.checked)}
          className="accent-emerald-500"
        />
        Create new repository
      </label>
    </div>

    <!-- File selection -->
    <div className="mt-2.5">
      <button
        onClick=${() => setShowFiles((v) => !v)}
        className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-slate-100"
      >
        <${ChevronDown} size=${14} className=${cx("transition", showFiles ? "rotate-0" : "-rotate-90")} />
        Choose files (${chosen.length}/${all.length})
      </button>
      ${showFiles &&
      html`<div className="mt-2 grid grid-cols-1 gap-1 sm:grid-cols-2">
        ${all.map(
          (a) => html`<label
            key=${a.name}
            className="flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5 text-xs text-slate-200"
          >
            <input
              type="checkbox"
              checked=${!deselected[a.name]}
              onChange=${() => toggle(a.name)}
              className="accent-indigo-500"
            />
            <span className="truncate font-mono" title=${a.name}>${a.name}</span>
          </label>`
        )}
      </div>`}
    </div>

    ${result &&
    html`<div className="mt-3 rounded-lg border border-white/10 bg-white/[0.03] p-3">
      <div className="flex items-center gap-2 text-sm">
        <span
          className="rounded border border-indigo-400/40 bg-indigo-400/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-200"
          >${result.mode === "new_repo" ? "new repo" : "pull request"}${result.dry_run ? " · dry-run" : ""}</span
        >
        <a
          href=${result.html_url}
          target="_blank"
          rel="noreferrer"
          className="font-mono text-xs text-indigo-300 hover:underline"
          >${result.html_url}</a
        >
      </div>
      <p className="mt-1.5 pl-0.5 text-xs text-slate-400">
        ${result.files} file(s) → <span className="font-mono text-slate-300">${result.repo}</span>
        on branch <span className="font-mono text-slate-300">${result.branch}</span>
        ${result.pull_request ? html` · PR #${result.pull_request.number}` : " (pushed)"}
      </p>
      ${result.commit && result.commit.subject
        ? html`<p className="mt-1 pl-0.5 text-xs text-slate-500">
            <span className="text-slate-400">AI commit:</span>
            <span className="ml-1 font-mono text-slate-300">${result.commit.subject}</span>
          </p>`
        : null}
    </div>`}
  </div>`;
}


function RepoContextPanel({ ctx }) {
  if (!ctx) return null;
  const { repo, files, error } = ctx;
  const list = files || [];
  return html`<div
    className="sdlc-fade rounded-2xl border border-indigo-400/30 bg-indigo-400/[0.06] p-4 shadow-soft"
  >
    <div className="flex items-center gap-2.5">
      <div className="grid h-9 w-9 place-items-center rounded-lg border border-indigo-400/40 bg-indigo-400/15 text-indigo-300">
        <${GitBranch} size=${16} />
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-100">
          ${error ? "Could not load repository" : `Editing existing repo · ${repo}`}
          ${!error &&
          html`<span className="text-slate-400"> · ${list.length} file${list.length === 1 ? "" : "s"} loaded</span>`}
        </p>
        <p className="text-xs text-slate-400">
          ${error
            ? error
            : "Read from the repo and given to the agents as context to edit in place — the result publishes as a branch + PR."}
        </p>
      </div>
    </div>
    ${!error && list.length
      ? html`<div className="mt-3 flex flex-wrap gap-1.5">
          ${list.map(
            (f) => html`<span
              key=${f.path}
              className="inline-flex items-center gap-1 rounded border border-indigo-400/30 bg-indigo-400/10 px-1.5 py-0.5 font-mono text-[10px] text-indigo-200"
              >${f.path}</span
            >`
          )}
        </div>`
      : null}
  </div>`;
}


function GroundingPanel({ grounding }) {
  if (!grounding || !(grounding.citations || []).length) return null;
  const { label, citations, subqueries } = grounding;
  return html`<div
    className="sdlc-fade rounded-2xl border border-violet-400/30 bg-violet-400/[0.06] p-4 shadow-soft"
  >
    <div className="flex items-center gap-2.5">
      <div className="grid h-9 w-9 place-items-center rounded-lg border border-violet-400/40 bg-violet-400/15 text-violet-300">
        <${BookOpen} size=${16} />
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-100">
          Grounded with ${label || "Foundry IQ"}
          <span className="text-slate-400"> · ${citations.length} source${citations.length === 1 ? "" : "s"}</span>
        </p>
        <p className="text-xs text-slate-400">
          Cited company standards injected into the Requirements & Architect agents to reduce hallucination.
        </p>
      </div>
    </div>
    ${subqueries && subqueries.length
      ? html`<div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wide text-slate-500">agentic sub-queries</span>
          ${subqueries.map(
            (q) => html`<span
              className="rounded border border-violet-400/30 bg-violet-400/10 px-1.5 py-0.5 text-[10px] text-violet-200"
              >${q}</span
            >`
          )}
        </div>`
      : null}
    <ul className="mt-3 space-y-2">
      ${citations.map(
        (c) => html`<li
          key=${c.id}
          className="rounded-lg border border-white/10 bg-white/[0.03] p-2"
        >
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-violet-400/40 bg-violet-400/10 px-1.5 py-0.5 font-mono text-[10px] text-violet-200">${c.id}</span>
            <span className="text-xs font-semibold text-slate-200">${c.title}</span>
            ${c.source
              ? html`<span className="font-mono text-[10px] text-slate-500">${c.source}</span>`
              : null}
          </div>
          ${c.snippet
            ? html`<p className="mt-1 pl-1 text-xs leading-relaxed text-slate-400">${c.snippet}</p>`
            : null}
        </li>`
      )}
    </ul>
  </div>`;
}

/* --------------------------------------------------------- JiraPublish */
function JiraPublish({ bundle, jira, creating, created, onCreate }) {
  if (!bundle || !(bundle.stories || []).length) return null;
  const n = bundle.stories.length;
  const subCount = bundle.stories.reduce((a, s) => a + ((s.subtasks || []).length), 0);
  return html`<div
    className="sdlc-fade rounded-2xl border border-sky-400/30 bg-sky-400/[0.06] p-4 shadow-soft"
  >
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2.5">
        <div className="grid h-9 w-9 place-items-center rounded-lg border border-sky-400/40 bg-sky-400/15 text-sky-300">
          <${Ticket} size=${16} />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-100">
            ${n} story${n === 1 ? "" : "ies"} ready for JIRA
            ${subCount
              ? html`<span className="text-slate-400"> · ${subCount} sub-task${subCount === 1 ? "" : "s"}</span>`
              : null}
            ${bundle.epic
              ? html`<span className="text-slate-400"> · under epic "${bundle.epic.summary}"</span>`
              : null}
          </p>
          <p className="text-xs text-slate-400">
            ${jira && jira.is_mock
              ? "Mock mode — creates demo keys, nothing leaves your machine."
              : jira
              ? `Creates real issues in ${jira.host} (${jira.project_key}).`
              : "JIRA status unavailable."}
            ${jira && jira.default_assignee
              ? html`<span className="text-slate-500"> · assignee: ${jira.default_assignee}</span>`
              : null}
          </p>
        </div>
      </div>
      <button
        onClick=${() => onCreate(bundle)}
        disabled=${creating}
        className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-b from-sky-500 to-sky-600 px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
      >
        ${creating ? html`<${Spinner} />` : html`<${Ticket} size=${15} />`}
        ${creating ? "Creating…" : `Create ${n} in JIRA`}
      </button>
    </div>

    ${created &&
    html`<div className="mt-3 border-t border-white/10 pt-3">
      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Created issues
      </p>
      ${created.epic &&
      html`<a
        href=${created.epic.url}
        target="_blank"
        rel="noreferrer"
        className="mb-2 inline-flex items-center gap-1.5 rounded-lg border border-violet-400/40 bg-violet-400/10 px-2.5 py-1 font-mono text-xs text-violet-200 hover:bg-violet-400/20"
        >${created.epic.key} (epic)</a
      >`}
      <ul className="space-y-2">
        ${(created.created || []).map(
          (c) => html`<li
            key=${c.key}
            className="rounded-lg border border-white/10 bg-white/[0.03] p-2"
          >
            <div className="flex flex-wrap items-center gap-2">
              <a
                href=${c.url}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-sky-400/40 bg-sky-400/10 px-2 py-0.5 font-mono text-xs text-sky-200 hover:bg-sky-400/20"
                >${c.key}</a
              >
              <span className="min-w-0 flex-1 truncate text-xs text-slate-300">${c.summary}</span>
              ${c.assignee &&
              html`<span
                title=${"Assignee: " + c.assignee}
                className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300"
                >👤 ${c.assignee}</span
              >`}
            </div>
            ${(c.subtasks || []).length > 0 &&
            html`<div className="mt-1.5 flex flex-wrap items-center gap-1.5 pl-3">
              <span className="text-[10px] uppercase tracking-wide text-slate-500">sub-tasks</span>
              ${c.subtasks.map(
                (st) => html`<a
                  key=${st.key}
                  href=${st.url}
                  target="_blank"
                  rel="noreferrer"
                  title=${st.summary}
                  className="inline-flex items-center gap-1 rounded border border-slate-400/30 bg-slate-400/10 px-1.5 py-0.5 font-mono text-[10px] text-slate-300 hover:bg-slate-400/20"
                  >↳ ${st.key}</a
                >`
              )}
            </div>`}
          </li>`
        )}
      </ul>
    </div>`}
  </div>`;
}

/** Parse the stories.json artifact (if present) into a bundle object. */
function useStoryBundle(artifacts) {
  return useMemo(() => {
    const art = artifacts["stories.json"];
    if (!art) return null;
    try {
      const data = JSON.parse(art.content);
      const stories = Array.isArray(data) ? data : data.stories || [];
      const epic = Array.isArray(data) ? null : data.epic || null;
      return stories.length ? { stories, epic } : null;
    } catch (_) {
      return null;
    }
  }, [artifacts]);
}

function App() {
  const s = useAgentStream();
  const running = s.runStatus === "running";
  const [toast, setToast] = useState(null);
  const notify = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 1600);
  }, []);

  const jira = useJira(notify);
  const github = useGitHub(notify);
  const admin = useAdmin(notify);
  const bundle = useStoryBundle(s.artifacts);

  // Clear previously-created issues when a new run starts.
  useEffect(() => {
    if (s.runStatus === "running") jira.reset();
    if (s.runStatus === "running") github.reset();
  }, [s.runStatus]);

  // Keep header badges in sync after a runtime provider switch.
  useEffect(() => {
    if (admin.state) {
      jira.refresh();
      github.refresh();
    }
  }, [admin.state]);

  return html`<div className="min-h-full">
    <${Header}
      config=${s.config}
      providerLabel=${s.providerLabel}
      runStatus=${s.runStatus}
      durationMs=${s.durationMs}
      jira=${jira.status}
      github=${github.status}
      admin=${admin}
    />
    <main className="mx-auto max-w-[1400px] px-6 py-6">
      <${Composer}
        running=${running}
        onRun=${s.run}
        onStop=${s.stop}
        jira=${jira.status}
        repos=${github.repos}
        notify=${notify}
      />

      ${s.repoContext
        ? html`<div className="mt-4">
            <${RepoContextPanel} ctx=${s.repoContext} />
          </div>`
        : null}

      ${s.grounding && (s.grounding.citations || []).length
        ? html`<div className="mt-4">
            <${GroundingPanel} grounding=${s.grounding} />
          </div>`
        : null}

      ${bundle &&
      html`<div className="mt-4">
        <${JiraPublish}
          bundle=${bundle}
          jira=${jira.status}
          creating=${jira.creating}
          created=${jira.created}
          onCreate=${jira.createStories}
        />
      </div>`}

      ${s.artifactOrder.length > 0
        ? html`<div className="mt-4">
            <${GitHubPublish}
              artifacts=${s.artifacts}
              title=${s.request}
              github=${github.status}
              repos=${github.repos}
              editRepo=${s.repoContext && !s.repoContext.error ? s.repoContext.repo : ""}
              publishing=${github.publishing}
              result=${github.result}
              onPublish=${github.publish}
            />
          </div>`
        : null}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1.15fr_1fr]">
        <section>
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              Pipeline
            </span>
            <span className="text-xs text-slate-500">${statusText(s.runStatus, s.durationMs)}</span>
          </div>
          <${Pipeline} agentOrder=${s.agentOrder} agents=${s.agents} loops=${s.loops} />
        </section>

        <section className="lg:sticky lg:top-[84px] lg:h-[calc(100vh-108px)]">
          <${ArtifactPanel} artifactOrder=${s.artifactOrder} artifacts=${s.artifacts} notify=${notify} />
        </section>
      </div>
    </main>

    ${toast &&
    html`<div
      className="fixed bottom-5 left-1/2 -translate-x-1/2 rounded-xl border border-white/10 bg-ink-800/90 px-4 py-2.5 text-sm text-slate-100 shadow-soft backdrop-blur-xl"
    >
      ${toast}
    </div>`}
  </div>`;
}

createRoot(document.getElementById("root")).render(html`<${App} />`);

