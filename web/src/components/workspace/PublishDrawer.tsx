import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { GitBranch, GitPullRequest, Github, Loader2, Plus, X } from "lucide-react";
import type { Artifact, PublishMode, PublishOptions, PublishResult } from "../../lib/types";

interface GitHubStatusLite {
  is_mock: boolean;
  owner?: string;
  repo?: string;
  has_default_repo?: boolean;
}

interface Props {
  open: boolean;
  onClose: () => void;
  files: Artifact[];
  repos: string[];
  defaultRepo: string;
  defaultBranch: string;
  defaultTitle: string;
  github: GitHubStatusLite | null;
  publishing: boolean;
  result: PublishResult | null;
  onPublish: (files: Artifact[], title: string, opts: PublishOptions) => void;
}

/**
 * Right-side publish drawer (UI_SPEC §12). Choose the target repo + branch, a
 * publish mode (open PR against an existing repo, or create a new repo), and a
 * commit message — then ship only the selected files. Never auto-publishes.
 */
export default function PublishDrawer({
  open,
  onClose,
  files,
  repos,
  defaultRepo,
  defaultBranch,
  defaultTitle,
  github,
  publishing,
  result,
  onPublish,
}: Readonly<Props>) {
  const ownerOnly = !!(github && github.has_default_repo === false && !github.is_mock);
  const [repo, setRepo] = useState(defaultRepo);
  const [branch, setBranch] = useState(defaultBranch);
  const [mode, setMode] = useState<PublishMode>(ownerOnly ? "new_repo" : "pr");
  const [message, setMessage] = useState(defaultTitle);

  // Re-seed each time the drawer opens so it reflects the latest context.
  useEffect(() => {
    if (!open) return;
    setRepo(defaultRepo);
    setBranch(defaultBranch);
    setMessage(defaultTitle);
    setMode(ownerOnly ? "new_repo" : "pr");
  }, [open, defaultRepo, defaultBranch, defaultTitle, ownerOnly]);

  const createNew = mode === "new_repo";
  const repoOk = repo.includes("/") || (createNew && ownerOnly);
  const canPublish = !publishing && files.length > 0 && repoOk;

  const submit = () =>
    onPublish(files, message || defaultTitle, { repo, createNew, branch });

  const MODES: { key: PublishMode; label: string; icon: typeof GitPullRequest; hint: string }[] = [
    { key: "pr", label: "Open Pull Request", icon: GitPullRequest, hint: "Branch + PR against an existing repo" },
    { key: "new_repo", label: "Create new repository", icon: Plus, hint: "Auto-named new repo, then push" },
  ];

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[70] flex justify-end bg-black/50 backdrop-blur-sm"
          onMouseDown={onClose}
        >
          <motion.aside
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 40, opacity: 0 }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
            onMouseDown={(e) => e.stopPropagation()}
            className="flex h-full w-full max-w-md flex-col border-l border-white/10 bg-ink-900/95 shadow-soft backdrop-blur-xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div className="flex items-center gap-2.5">
                <span className="grid h-9 w-9 place-items-center rounded-lg border border-indigo-400/40 bg-indigo-400/15 text-indigo-300">
                  <Github className="h-4 w-4" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-100">Publish to GitHub</p>
                  <p className="text-xs text-slate-500">
                    {github?.is_mock ? "Mock — simulates the action offline" : "Human-in-the-loop"}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="rounded-md p-1 text-slate-400 transition hover:text-slate-200"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 space-y-4 overflow-auto px-5 py-4">
              {/* Mode */}
              <div>
                <p className="mb-1.5 label-caps">Mode</p>
                <div className="grid gap-2">
                  {MODES.map((m) => (
                    <button
                      key={m.key}
                      onClick={() => setMode(m.key)}
                      className={[
                        "flex items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition",
                        mode === m.key
                          ? "border-accent-500/50 bg-accent-500/10"
                          : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]",
                      ].join(" ")}
                    >
                      <m.icon
                        className={["h-4 w-4", mode === m.key ? "text-accent-300" : "text-slate-400"].join(" ")}
                      />
                      <span className="min-w-0">
                        <span className="block text-sm font-semibold text-slate-100">{m.label}</span>
                        <span className="block text-[11px] text-slate-500">{m.hint}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Repo */}
              <div>
                <label className="mb-1.5 block label-caps" htmlFor="pub-repo">
                  Target repo
                </label>
                <input
                  id="pub-repo"
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  list="pub-repo-options"
                  placeholder={ownerOnly ? "blank = auto-named, or owner/name" : "owner/name"}
                  spellCheck={false}
                  className="w-full rounded-lg border border-white/10 bg-ink-950/60 px-3 py-2 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-accent-500 focus:outline-none"
                />
                <datalist id="pub-repo-options">
                  {repos.map((r) => (
                    <option key={r} value={r} />
                  ))}
                </datalist>
              </div>

              {/* Branch */}
              <div>
                <label className="mb-1.5 block label-caps" htmlFor="pub-branch">
                  Branch
                </label>
                <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-ink-950/60 px-3 py-2 focus-within:border-accent-500">
                  <GitBranch className="h-4 w-4 shrink-0 text-slate-500" />
                  <input
                    id="pub-branch"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    placeholder="auto"
                    spellCheck={false}
                    className="w-full bg-transparent font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none"
                  />
                </div>
                <p className="mt-1 text-[11px] text-slate-500">
                  Leave blank to let the agent name the feature branch.
                </p>
              </div>

              {/* Commit message */}
              <div>
                <label className="mb-1.5 block label-caps" htmlFor="pub-msg">
                  Commit / PR title
                </label>
                <textarea
                  id="pub-msg"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={2}
                  placeholder="Add JWT auth module with tests"
                  className="w-full resize-y rounded-lg border border-white/10 bg-ink-950/60 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:border-accent-500 focus:outline-none"
                />
              </div>

              {/* Selected files */}
              <div>
                <p className="mb-1.5 label-caps">Files ({files.length})</p>
                <div className="max-h-40 space-y-1 overflow-auto rounded-lg border border-white/10 bg-white/[0.02] p-2">
                  {files.map((f) => (
                    <div
                      key={f.name}
                      className="truncate font-mono text-[11px] text-slate-300"
                      title={f.name}
                    >
                      {f.name}
                    </div>
                  ))}
                </div>
              </div>

              {result && (
                <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="rounded border border-indigo-400/40 bg-indigo-400/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-200">
                      {result.mode === "new_repo" ? "new repo" : "pull request"}
                      {result.dry_run ? " · dry-run" : ""}
                    </span>
                    <a
                      href={result.html_url}
                      target="_blank"
                      rel="noreferrer"
                      className="truncate font-mono text-xs text-indigo-300 hover:underline"
                    >
                      {result.html_url}
                    </a>
                  </div>
                  {result.commit?.subject && (
                    <p className="mt-1.5 text-[11px] text-slate-500">
                      <span className="text-slate-400">AI commit:</span>{" "}
                      <span className="font-mono text-slate-300">{result.commit.subject}</span>
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Footer actions */}
            <div className="flex items-center justify-end gap-2 border-t border-white/10 px-5 py-4">
              <button
                onClick={onClose}
                className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-sm font-semibold text-slate-300 transition hover:bg-white/[0.07]"
              >
                Cancel
              </button>
              <button
                onClick={submit}
                disabled={!canPublish}
                title={canPublish ? "" : "Enter a target repo as owner/name (or pick create-new)."}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-b from-accent-500 to-accent-600 px-4 py-2 text-sm font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5 disabled:opacity-50"
              >
                {publishing ? <Loader2 className="h-4 w-4 animate-spin" /> : <GitPullRequest className="h-4 w-4" />}
                {createNew ? "Create repo & push" : "Open PR"}
              </button>
            </div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

