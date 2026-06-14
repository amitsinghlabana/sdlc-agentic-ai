import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, GitBranch, Github, Loader2 } from "lucide-react";
import type { Artifact, PublishOptions, PublishResult } from "../lib/types";

interface GitHubStatusLite {
  is_mock: boolean;
  owner?: string;
  repo?: string;
  has_default_repo?: boolean;
}

interface Props {
  artifacts: Record<string, Artifact>;
  title: string;
  github: GitHubStatusLite | null;
  repos: string[];
  /** Repo whose code we just edited (edit-existing-repo mode), else "". */
  editRepo: string;
  publishing: boolean;
  result: PublishResult | null;
  onPublish: (files: Artifact[], title: string, opts: PublishOptions) => void;
}

/**
 * Human-in-the-loop "Publish to GitHub" panel shown after a run produces
 * artifacts. Pick which files to include and a target repo, then open a branch
 * + PR (existing repo) or create a new repo. Restores the action that lived in
 * the original UI; wired to POST /api/github/publish via useGitHub().publish.
 */
export default function GitHubPublishPanel({
  artifacts,
  title,
  github,
  repos,
  editRepo,
  publishing,
  result,
  onPublish,
}: Readonly<Props>) {
  const all = Object.values(artifacts ?? {}).filter(
    (a) => a.name !== "stories.json" && (a.content || "").trim(),
  );
  const [deselected, setDeselected] = useState<Record<string, boolean>>({});
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

  if (all.length === 0) return null;

  const isMock = github ? github.is_mock : true;
  const chosen = all.filter((a) => !deselected[a.name]);
  const toggle = (name: string) => setDeselected((d) => ({ ...d, [name]: !d[name] }));
  const repoOk = repo.includes("/") || (ownerOnly && createNew);
  const canPublish = !publishing && chosen.length > 0 && repoOk;
  const ownerLabel = github && github.owner ? github.owner : "your account";

  let blurb: string;
  if (isMock) {
    blurb = "GitHub mock — no account; simulates the chosen action offline.";
  } else if (createNew) {
    blurb = repo.includes("/")
      ? `Creates new repo ${repo} and pushes the selected files.`
      : `Creates a new repo under ${ownerLabel} (auto-named) and pushes the selected files.`;
  } else {
    blurb = "Opens a branch + PR with the selected files.";
  }

  let publishLabel: string;
  if (publishing) publishLabel = "Publishing…";
  else if (createNew) publishLabel = "Create repo & push";
  else publishLabel = "Open PR";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-card border border-indigo-400/30 bg-indigo-400/[0.06] p-4 shadow-soft"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-lg border border-indigo-400/40 bg-indigo-400/15 text-indigo-300">
            <Github className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-100">
              Publish to GitHub
              <span className="text-slate-400">
                {" "}
                · {chosen.length} of {all.length} file{all.length === 1 ? "" : "s"}
              </span>
            </p>
            <p className="text-xs text-slate-400">{blurb}</p>
          </div>
        </div>
        <button
          onClick={() => onPublish(chosen, title, { repo, createNew })}
          disabled={!canPublish}
          title={
            canPublish
              ? ""
              : ownerOnly
                ? "Tick 'Create new repository' or enter owner/name"
                : "Enter a repo as owner/name"
          }
          className="inline-flex items-center gap-2 rounded-lg border border-indigo-400/40 bg-indigo-400/15 px-3.5 py-2 text-sm font-semibold text-indigo-200 transition hover:bg-indigo-400/25 disabled:opacity-50"
        >
          {publishing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <GitBranch className="h-4 w-4" />
          )}
          {publishLabel}
        </button>
      </div>

      {/* Repo picker + create-new */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-[11px] uppercase tracking-wide text-slate-500">Repo</span>
        <input
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          list="gh-publish-repo-options"
          placeholder={ownerOnly ? "blank = auto-named, or name / owner/name" : "owner/name"}
          spellCheck={false}
          className="min-w-[220px] flex-1 rounded-lg border border-white/10 bg-ink-900/60 px-2.5 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
        />
        <datalist id="gh-publish-repo-options">
          {repos.map((r) => (
            <option key={r} value={r} />
          ))}
        </datalist>
        <label
          className={[
            "inline-flex cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs transition",
            createNew
              ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-200"
              : "border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.06]",
          ].join(" ")}
        >
          <input
            type="checkbox"
            checked={createNew}
            onChange={(e) => setCreateNew(e.target.checked)}
            className="accent-emerald-500"
          />
          Create new repository
        </label>
      </div>

      {/* File selection */}
      <div className="mt-2.5">
        <button
          onClick={() => setShowFiles((v) => !v)}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-300 transition hover:text-slate-100"
        >
          <ChevronDown
            className={["h-3.5 w-3.5 transition", showFiles ? "rotate-0" : "-rotate-90"].join(" ")}
          />
          Choose files ({chosen.length}/{all.length})
        </button>
        {showFiles && (
          <div className="mt-2 grid grid-cols-1 gap-1 sm:grid-cols-2">
            {all.map((a) => (
              <label
                key={a.name}
                className="flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5 text-xs text-slate-200"
              >
                <input
                  type="checkbox"
                  checked={!deselected[a.name]}
                  onChange={() => toggle(a.name)}
                  className="accent-indigo-500"
                />
                <span className="truncate font-mono" title={a.name}>
                  {a.name}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>

      {result && (
        <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.03] p-3">
          <div className="flex items-center gap-2 text-sm">
            <span className="rounded border border-indigo-400/40 bg-indigo-400/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-200">
              {result.mode === "new_repo" ? "new repo" : "pull request"}
              {result.dry_run ? " · dry-run" : ""}
            </span>
            <a
              href={result.html_url}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-xs text-indigo-300 hover:underline"
            >
              {result.html_url}
            </a>
          </div>
          <p className="mt-1.5 pl-0.5 text-xs text-slate-400">
            {result.files} file(s) →{" "}
            <span className="font-mono text-slate-300">{result.repo}</span> on branch{" "}
            <span className="font-mono text-slate-300">{result.branch}</span>
            {result.pull_request ? ` · PR #${result.pull_request.number}` : " (pushed)"}
          </p>
          {result.commit?.subject && (
            <p className="mt-1 pl-0.5 text-xs text-slate-500">
              <span className="text-slate-400">AI commit:</span>
              <span className="ml-1 font-mono text-slate-300">{result.commit.subject}</span>
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}

