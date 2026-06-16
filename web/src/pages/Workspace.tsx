import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import RequirementComposer from "../components/workspace/RequirementComposer";
import WorkspaceTopBar from "../components/workspace/WorkspaceTopBar";
import Sidebar from "../components/shell/Sidebar";
import PipelineTracker from "../components/workspace/PipelineTracker";
import ChatPipeline from "../components/workspace/ChatPipeline";
import ArtifactExplorer from "../components/workspace/ArtifactExplorer";
import FileSelectionSummary from "../components/workspace/FileSelectionSummary";
import PublishDrawer from "../components/workspace/PublishDrawer";
import RepoContextPanel from "../components/RepoContextPanel";
import JiraPublishPanel from "../components/JiraPublishPanel";
import { useAgentStream } from "../hooks/useAgentStream";
import { useAdmin } from "../hooks/useAdmin";
import { useGitHub } from "../hooks/useGitHub";
import { useJira } from "../hooks/useJira";
import { useStoryBundle } from "../hooks/useStoryBundle";
import { addRun, rid } from "../store/useRunStore";
import { toast } from "../store/toast";


function statusLabel(runStatus: string, durationMs: number | null): string {
  if (runStatus === "idle") return "idle";
  if (runStatus === "running") return "running…";
  if (runStatus === "done") {
    return durationMs == null ? "done" : `done in ${(durationMs / 1000).toFixed(1)}s`;
  }
  return runStatus;
}

/**
 * The product workspace (APP_WORKSPACE_BUILD_SPEC): a 3-column layout — icon
 * mini-nav, center requirement composer + live pipeline, and a VS Code-style
 * artifacts explorer with per-file selection feeding a GitHub publish drawer.
 * SSE wiring (useAgentStream) is preserved verbatim.
 */
export default function Workspace() {
  const {
    config,
    run,
    stop,
    runStatus,
    request,
    agentOrder,
    agents,
    artifactOrder,
    artifacts,
    loops,
    repoContext,
    durationMs,
    providerLabel,
  } = useAgentStream();

  const notify = useCallback((msg: string) => toast(msg), []);
  const admin = useAdmin(notify);
  const github = useGitHub();
  const jira = useJira();
  const storyBundle = useStoryBundle(artifacts);
  // The JIRA issue imported into the composer (drives context-aware create:
  // sub-tasks under a Story, stories under an Epic, vs. a fresh epic+stories).
  const [importedIssue, setImportedIssue] = useState<
    { key: string; type: string; summary?: string } | null
  >(null);

  const running = runStatus === "running";

  // ---- Composer state (controlled, so the top bar can also Run/Stop) -------- #
  // Start blank so the placeholder hint guides the user; sample chips or JIRA
  // import can fill it in. (No pre-filled "actual prompt".)
  const [title, setTitle] = useState("");
  const [value, setValue] = useState("");
  const [editRepo, setEditRepo] = useState(false);
  const [repo, setRepo] = useState("");

  // ---- Publish target (repo + branch) — chosen in the publish drawer ------- #
  const [project, setProject] = useState("");
  const [branch] = useState("main");

  // ---- Publish selection + drawer ------------------------------------------ #
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [publishOpen, setPublishOpen] = useState(false);

  // Seed the publish target: prefer the repo being edited, else the default.
  useEffect(() => {
    if (github.status?.repo) setProject((p) => p || github.status!.repo);
  }, [github.status]);
  useEffect(() => {
    if (repoContext && !repoContext.error && repoContext.repo) setProject(repoContext.repo);
  }, [repoContext]);

  // Clear previously-published results when a new run starts.
  // NOTE: depend on the *stable* reset callbacks (useCallback), not the whole
  // github/jira hook objects — those are re-created every render, which would
  // re-fire this effect on every render and wipe the file selection mid-run.
  const { reset: resetGitHub } = github;
  const { reset: resetJira } = jira;
  useEffect(() => {
    if (runStatus === "running") {
      resetGitHub();
      resetJira();
      setSelected(new Set());
    }
  }, [runStatus, resetGitHub, resetJira]);

  // Keep publish targets in sync ONLY after a real runtime provider switch.
  // The github/jira hooks already fetch on mount, so we skip the *initial*
  // admin load (first non-null state) to avoid a redundant second fetch.
  // We also depend on the *stable* refresh callbacks + admin.state only —
  // depending on the whole github/jira objects (new refs each render) caused an
  // infinite refresh → fetch → setState → render loop (the continuous
  // /api/github/repos and /api/jira/status calls seen in the server logs).
  const { refresh: refreshGitHub } = github;
  const { refresh: refreshJira } = jira;
  const adminSyncedRef = useRef(false);
  useEffect(() => {
    if (!admin.state) return;
    if (!adminSyncedRef.current) {
      adminSyncedRef.current = true; // initial load — mount fetch already ran
      return;
    }
    refreshGitHub();
    refreshJira();
  }, [admin.state, refreshGitHub, refreshJira]);

  // ---- Run recording for the Dashboard (does not touch the SSE hook) -------- #
  const lastReqRef = useRef("");
  const lastRepoRef = useRef<string | null>(null);
  const startedAtRef = useRef(0);
  const recordedRef = useRef(false);

  const handleRun = useCallback(() => {
    const req = value.trim();
    if (!req) {
      toast("Describe a feature to run the team — type a sentence or pick a sample below.");
      return;
    }
    const targetRepo = editRepo ? repo : undefined;
    lastReqRef.current = req;
    lastRepoRef.current = targetRepo ?? null;
    startedAtRef.current = Date.now();
    recordedRef.current = false;
    run(req, targetRepo);
  }, [value, editRepo, repo, run]);

  const handleRetry = useCallback(() => {
    if (!lastReqRef.current) return;
    startedAtRef.current = Date.now();
    recordedRef.current = false;
    run(lastReqRef.current, lastRepoRef.current ?? undefined);
  }, [run]);

  useEffect(() => {
    if (runStatus === "running" || runStatus === "idle") {
      recordedRef.current = false;
      return;
    }
    if (!recordedRef.current && lastReqRef.current) {
      recordedRef.current = true;
      addRun({
        id: rid(),
        request: lastReqRef.current,
        status: runStatus,
        durationMs,
        artifacts: artifactOrder.length,
        provider: providerLabel,
        repo: lastRepoRef.current,
        startedAt: startedAtRef.current || Date.now(),
      });
    }
  }, [runStatus, durationMs, artifactOrder.length, providerLabel]);

  // ---- Selection helpers ---------------------------------------------------- #
  const toggleSelect = useCallback((name: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelected((prev) =>
      prev.size === artifactOrder.length ? new Set() : new Set(artifactOrder),
    );
  }, [artifactOrder]);

  const selectedFiles = useMemo(
    () => artifactOrder.filter((n) => selected.has(n)).map((n) => artifacts[n]).filter(Boolean),
    [selected, artifactOrder, artifacts],
  );

  const publishTitle = title.trim() || request || value;

  return (
    <div className="flex min-h-screen">
      {/* Shared left navigation — consistent across every in-app screen */}
      <Sidebar />

      {/* Content column: workspace top bar + two-column body */}
      <div className="flex min-w-0 flex-1 flex-col">
        <WorkspaceTopBar
          runStatus={runStatus}
          durationMs={durationMs}
          running={running}
          onRun={handleRun}
          onStop={stop}
          onRetry={handleRetry}
          canRetry={!!lastReqRef.current}
          onPublish={() => setPublishOpen(true)}
          publishCount={selectedFiles.length}
          admin={admin}
          adminState={admin.state}
          github={github.status}
          jira={jira.status}
          llmLabel={providerLabel ?? config?.provider_label ?? "LLM"}
        />

        <div className="mx-auto grid w-full max-w-[1500px] grid-cols-1 gap-5 px-4 py-5 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
            {/* Center: composer + pipeline */}
            <div id="pipeline-col" className="min-w-0 space-y-4">
              <RequirementComposer
                running={running}
                title={title}
                onTitleChange={setTitle}
                value={value}
                onValueChange={setValue}
                editRepo={editRepo}
                onEditRepoChange={setEditRepo}
                repo={repo}
                onRepoChange={setRepo}
                repos={github.repos}
                jira={jira.status}
                onImported={setImportedIssue}
                onRun={handleRun}
                onStop={stop}
              />

              {repoContext && <RepoContextPanel ctx={repoContext} />}

              {storyBundle && (
                <JiraPublishPanel
                  bundle={storyBundle}
                  jira={jira.status}
                  creating={jira.creating}
                  created={jira.created}
                  imported={importedIssue}
                  onCreate={(b) => jira.createStories(b, importedIssue)}
                />
              )}

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="label-caps">Pipeline</span>
                  <span className="text-xs text-slate-500">{statusLabel(runStatus, durationMs)}</span>
                </div>
                <PipelineTracker agentOrder={agentOrder} agents={agents} />
                <ChatPipeline agentOrder={agentOrder} agents={agents} loops={loops} />
              </div>
            </div>

            {/* Right: artifacts explorer + selection summary */}
            <div
              id="files-col"
              className="flex min-w-0 flex-col gap-3 lg:sticky lg:top-[4.5rem] lg:h-[calc(100vh-5.5rem)]"
            >
              <div className="min-h-[360px] flex-1 lg:min-h-0">
                <ArtifactExplorer
                  artifactOrder={artifactOrder}
                  artifacts={artifacts}
                  selected={selected}
                  onToggleSelect={toggleSelect}
                  onSelectAll={selectAll}
                />
              </div>
              <FileSelectionSummary
                files={selectedFiles}
                onClear={() => setSelected(new Set())}
                onRemove={toggleSelect}
                onPublish={() => setPublishOpen(true)}
                publishing={github.publishing}
              />
            </div>
          </div>
        </div>

      <PublishDrawer
        open={publishOpen}
        onClose={() => setPublishOpen(false)}
        files={selectedFiles}
        repos={github.repos}
        defaultRepo={project}
        defaultBranch={branch}
        defaultTitle={publishTitle}
        github={github.status}
        publishing={github.publishing}
        result={github.result}
        onPublish={github.publish}
      />
    </div>
  );
}

