// Event & data types mirroring the backend SSE contract (see orchestrator.py).

export interface Artifact {
  name: string;
  type: string; // markdown | code | test | config | doc
  language: string; // python | markdown | html | yaml | json | text
  content: string;
}

export interface PlanStep {
  id: string;
  name: string;
  emoji: string;
  role: string;
}

export type StreamEvent =
  | { type: "run_start"; request: string; provider: string; provider_label: string }
  | { type: "plan"; steps: PlanStep[] }
  | {
      type: "repo_context";
      repo: string | null;
      count: number;
      files: RepoContextFile[];
      error?: string | null;
    }
  | {
      type: "agent_start";
      agent: string;
      name: string;
      emoji: string;
      role: string;
      iteration: number;
    }
  | { type: "delta"; agent: string; text: string }
  | { type: "artifact"; agent: string; artifact: Artifact }
  | {
      type: "agent_done";
      agent: string;
      summary: string;
      verdict: string | null;
      comments: string[];
    }
  | { type: "loop"; iteration: number; comments: string[]; final?: boolean }
  | {
      type: "run_complete";
      duration_ms: number;
      artifacts: { name: string; type: string; language: string }[];
    }
  | { type: "error"; agent?: string; message: string };

export type AgentStatus =
  | "queued"
  | "working"
  | "done"
  | "approved"
  | "changes"
  | "error";

export interface AgentState {
  id: string;
  name: string;
  emoji: string;
  role: string;
  status: AgentStatus;
  stream: string;
  summary: string;
  iteration: number;
  verdict: string | null;
  comments: string[];
}

export type RunStatus = "idle" | "running" | "done" | "stopped" | "error";

export interface AppConfig {
  provider: string;
  provider_label: string;
  is_mock: boolean;
  max_review_loops: number;
}


// --- Edit an existing repo (P3): context loaded for the agents to edit ------ #
export interface RepoContextFile {
  path: string;
  bytes?: number;
}

export interface RepoContext {
  repo: string | null;
  count: number;
  files: RepoContextFile[];
  error: string | null;
}

// --- Runtime provider switching (/api/admin/providers) --------------------- #
export type ProviderKey = "llm" | "knowledge" | "jira" | "github";

export interface ProviderInfo {
  selected: string;
  effective: string;
  options: string[];
  configured?: boolean | Record<string, boolean>;
}

export interface AdminState {
  providers: Record<ProviderKey, ProviderInfo>;
  overrides: Record<string, string>;
  persisted_to: string;
}

// --- JIRA story push (stories.json → POST /api/jira/create-stories) --------- #
export interface Subtask {
  summary: string;
  description?: string;
}

export interface Story {
  summary: string;
  description?: string;
  acceptance_criteria?: string[];
  story_points?: number | null;
  labels?: string[];
  issue_type?: string;
  subtasks?: Subtask[];
  assignee?: string | null;
}

export interface Epic {
  summary: string;
  description?: string;
}

/** The structured `stories.json` artifact: an optional epic + stories. */
export interface StoryBundle {
  epic: Epic | null;
  stories: Story[];
}

export interface CreatedIssue {
  key: string;
  url: string;
  summary: string;
  issue_type?: string;
  assignee?: string | null;
  subtasks?: CreatedIssue[];
}

export interface JiraCreatedResult {
  epic: CreatedIssue | null;
  created: CreatedIssue[];
  count: number;
  provider: string;
  /** How the issues were created: "new" | "epic_children" | "subtasks". */
  mode?: string;
  /** Parent issue key the created items were attached to (when applicable). */
  parent?: string | null;
}

/** A JIRA issue imported into the Composer (drives context-aware create). */
export interface ImportedIssue {
  key: string;
  type: string; // "Epic" | "Story" | ...
  summary?: string;
}

// --- GitHub publish (selected artifacts → POST /api/github/publish) --------- #
export type PublishMode = "pr" | "new_repo";

export interface PublishOptions {
  repo?: string;
  createNew?: boolean;
  branch?: string;
}

export interface PublishResult {
  provider: string;
  mode: string; // "new_repo" | "pull_request"
  html_url: string;
  repo: string;
  branch: string;
  files: number;
  dry_run?: boolean;
  pull_request?: { number: number; url?: string } | null;
  commit?: { subject?: string; pr_body?: string } | null;
}

