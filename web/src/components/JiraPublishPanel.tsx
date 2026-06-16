import { motion } from "framer-motion";
import { Loader2, Ticket } from "lucide-react";
import type { ImportedIssue, JiraCreatedResult, StoryBundle } from "../lib/types";
import type { JiraStatus } from "../hooks/useJira";

interface Props {
  bundle: StoryBundle | null;
  jira: JiraStatus | null;
  creating: boolean;
  created: JiraCreatedResult | null;
  imported?: ImportedIssue | null;
  onCreate: (bundle: StoryBundle) => void;
}

interface Copy {
  heading: string;
  ctaLabel: string;
  blurb: string;
  showSubBadge: boolean;
  showNewEpic: boolean;
}

/** Mock-or-live blurb shared by all branches. */
function liveBlurb(jira: JiraStatus | null, fallback: string): string {
  if (jira?.is_mock) return "Mock mode — creates demo keys, nothing leaves your machine.";
  return fallback;
}

/** Context-aware copy: sub-tasks under a Story, stories under an Epic, or a new epic+stories. */
function buildCopy(
  bundle: StoryBundle,
  jira: JiraStatus | null,
  imported: ImportedIssue | null | undefined,
  creating: boolean,
): Copy {
  const n = bundle.stories.length;
  const story = n === 1 ? "story" : "stories";
  const importType = (imported?.type ?? "").toLowerCase();
  const isEpic = importType === "epic";
  const isStory = !!imported && !isEpic;
  const key = imported?.key ?? "";
  const host = jira?.host ?? "JIRA";

  if (isStory) {
    const subTotal = bundle.stories.reduce(
      (a, s) => a + (s.subtasks?.length ? s.subtasks.length : 1),
      0,
    );
    const subWord = subTotal === 1 ? "sub-task" : "sub-tasks";
    return {
      heading: `${subTotal} ${subWord} ready for ${key}`,
      ctaLabel: creating ? "Creating…" : `Add ${subTotal} ${subWord}`,
      blurb: liveBlurb(jira, `Creates sub-tasks under existing story ${key} in ${host}.`),
      showSubBadge: false,
      showNewEpic: false,
    };
  }
  if (isEpic) {
    return {
      heading: `${n} ${story} ready for epic ${key}`,
      ctaLabel: creating ? "Creating…" : `Add ${n} to ${key}`,
      blurb: liveBlurb(jira, `Links stories under existing epic ${key} in ${host}.`),
      showSubBadge: true,
      showNewEpic: false,
    };
  }
  const liveFallback = jira ? `Creates real issues in ${jira.host} (${jira.project_key}).` : "JIRA status unavailable.";
  return {
    heading: `${n} ${story} ready for JIRA`,
    ctaLabel: creating ? "Creating…" : `Create ${n} in JIRA`,
    blurb: liveBlurb(jira, liveFallback),
    showSubBadge: true,
    showNewEpic: true,
  };
}

/**
 * Human-in-the-loop "Push stories to JIRA" panel. Appears when a run produces a
 * `stories.json` artifact: review the generated stories/sub-tasks, then create
 * them in JIRA. Context-aware: an imported Epic links stories under it; an
 * imported Story creates sub-tasks under it; otherwise a new epic + stories.
 */
export default function JiraPublishPanel({
  bundle,
  jira,
  creating,
  created,
  imported,
  onCreate,
}: Readonly<Props>) {
  if (!bundle || (bundle.stories ?? []).length === 0) return null;

  const subCount = bundle.stories.reduce((a, s) => a + (s.subtasks?.length ?? 0), 0);
  const { heading, ctaLabel, blurb, showSubBadge, showNewEpic } = buildCopy(
    bundle,
    jira,
    imported,
    creating,
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-card border border-sky-400/30 bg-sky-400/[0.06] p-4 shadow-soft"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-lg border border-sky-400/40 bg-sky-400/15 text-sky-300">
            <Ticket className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-100">
              {heading}
              {showSubBadge && subCount > 0 && (
                <span className="text-slate-400">
                  {" "}
                  · {subCount} sub-task{subCount === 1 ? "" : "s"}
                </span>
              )}
              {showNewEpic && bundle.epic && (
                <span className="text-slate-400"> · under epic “{bundle.epic.summary}”</span>
              )}
            </p>
            <p className="text-xs text-slate-400">
              {blurb}
              {jira?.default_assignee && (
                <span className="text-slate-500"> · assignee: {jira.default_assignee}</span>
              )}
            </p>
          </div>
        </div>
        <button
          onClick={() => onCreate(bundle)}
          disabled={creating}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-b from-sky-500 to-sky-600 px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Ticket className="h-4 w-4" />}
          {ctaLabel}
        </button>
      </div>

      {created && (
        <div className="mt-3 border-t border-white/10 pt-3">
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Created issues
          </p>
          {created.epic && (
            <a
              href={created.epic.url}
              target="_blank"
              rel="noreferrer"
              className="mb-2 inline-flex items-center gap-1.5 rounded-lg border border-violet-400/40 bg-violet-400/10 px-2.5 py-1 font-mono text-xs text-violet-200 hover:bg-violet-400/20"
            >
              {created.epic.key} (epic)
            </a>
          )}
          <ul className="space-y-2">
            {(created.created ?? []).map((c) => (
              <li key={c.key} className="rounded-lg border border-white/10 bg-white/[0.03] p-2">
                <div className="flex flex-wrap items-center gap-2">
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-md border border-sky-400/40 bg-sky-400/10 px-2 py-0.5 font-mono text-xs text-sky-200 hover:bg-sky-400/20"
                  >
                    {c.key}
                  </a>
                  <span className="min-w-0 flex-1 truncate text-xs text-slate-300">{c.summary}</span>
                  {c.assignee && (
                    <span
                      title={"Assignee: " + c.assignee}
                      className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300"
                    >
                      👤 {c.assignee}
                    </span>
                  )}
                </div>
                {(c.subtasks ?? []).length > 0 && (
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5 pl-3">
                    <span className="text-[10px] uppercase tracking-wide text-slate-500">
                      sub-tasks
                    </span>
                    {(c.subtasks ?? []).map((st) => (
                      <a
                        key={st.key}
                        href={st.url}
                        target="_blank"
                        rel="noreferrer"
                        title={st.summary}
                        className="inline-flex items-center gap-1 rounded border border-slate-400/30 bg-slate-400/10 px-1.5 py-0.5 font-mono text-[10px] text-slate-300 hover:bg-slate-400/20"
                      >
                        ↳ {st.key}
                      </a>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}

