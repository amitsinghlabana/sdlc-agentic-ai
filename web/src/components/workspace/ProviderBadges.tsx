import type { ComponentType } from "react";
import { Sparkles, Github, Ticket } from "lucide-react";
import type { AdminState, ProviderKey } from "../../lib/types";
import type { JiraStatus } from "../../hooks/useJira";

interface GitHubStatusLite {
  is_mock: boolean;
  owner?: string;
  repo?: string;
  repo_url?: string;
  has_default_repo?: boolean;
}

interface Props {
  admin: AdminState | null;
  github: GitHubStatusLite | null;
  jira: JiraStatus | null;
  llmLabel: string;
}

interface PillProps {
  icon: ComponentType<{ className?: string }>;
  label: string;
  live: boolean;
  fellBack: boolean;
  liveColor: string;
  title: string;
}

function Pill({ icon: Icon, label, live, fellBack, liveColor, title }: Readonly<PillProps>) {
  const cls =
    !live || fellBack
      ? "border-amber-400/40 bg-amber-400/10 text-amber-300"
      : liveColor;
  return (
    <span
      title={title}
      className={[
        "hidden items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-xs font-semibold md:flex",
        cls,
      ].join(" ")}
    >
      <Icon className="h-3.5 w-3.5" />
      <span className="max-w-[160px] truncate">{label}</span>
    </span>
  );
}

function info(admin: AdminState | null, key: ProviderKey) {
  const p = admin?.providers?.[key];
  const selected = p?.selected ?? "mock";
  const effective = p?.effective ?? "mock";
  const live = effective !== "mock";
  const fellBack = selected !== "mock" && effective === "mock";
  return { live, fellBack };
}

/**
 * Live/Mock status pills for each integration (LLM · GitHub · JIRA), driven by
 * the admin provider state so they flip the instant a provider is toggled. The
 * GitHub pill surfaces the configured owner/repo; JIRA shows the host — so the
 * default target is always visible.
 */
export default function ProviderBadges({ admin, github, jira, llmLabel }: Readonly<Props>) {
  const llm = info(admin, "llm");
  const gh = info(admin, "github");
  const jr = info(admin, "jira");

  const repoTarget = github?.repo || github?.owner || "";
  let ghLabel: string;
  if (!gh.live || gh.fellBack) ghLabel = "GitHub: Mock";
  else ghLabel = repoTarget ? `GitHub: ${repoTarget}` : "GitHub: Live";

  let ghTitle: string;
  if (gh.fellBack) ghTitle = "GitHub set to live but not configured — using mock.";
  else if (!gh.live) ghTitle = "GitHub mock — nothing leaves your machine.";
  else if (github?.has_default_repo && github.repo) ghTitle = `Publishes to ${github.repo}`;
  else if (github?.owner) ghTitle = `Owner ${github.owner} — a new repo is auto-named on publish.`;
  else ghTitle = "GitHub live.";

  const jiraHost = jira?.host ?? "";
  let jrLabel: string;
  if (!jr.live || jr.fellBack) jrLabel = "JIRA: Mock";
  else jrLabel = jiraHost ? `JIRA: ${jiraHost}` : "JIRA: Live";

  let jrTitle: string;
  if (jr.fellBack) jrTitle = "JIRA set to live but not configured — using mock.";
  else if (!jr.live) jrTitle = "JIRA mock — nothing leaves your machine.";
  else jrTitle = jira ? `Connected to ${jira.host} (project ${jira.project_key})` : "JIRA live.";

  return (
    <div className="flex items-center gap-2">
      <Pill
        icon={Sparkles}
        label={llm.live && !llm.fellBack ? llmLabel : "Mock"}
        live={llm.live}
        fellBack={llm.fellBack}
        liveColor="border-emerald-400/40 bg-emerald-400/10 text-emerald-300"
        title={llm.live && !llm.fellBack ? "Live LLM provider." : "Free mock LLM — no tokens spent."}
      />
      <Pill
        icon={Github}
        label={ghLabel}
        live={gh.live}
        fellBack={gh.fellBack}
        liveColor="border-indigo-400/40 bg-indigo-400/10 text-indigo-300"
        title={ghTitle}
      />
      <Pill
        icon={Ticket}
        label={jrLabel}
        live={jr.live}
        fellBack={jr.fellBack}
        liveColor="border-sky-400/40 bg-sky-400/10 text-sky-300"
        title={jrTitle}
      />
    </div>
  );
}

