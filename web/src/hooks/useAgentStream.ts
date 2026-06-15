import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentState,
  AppConfig,
  Artifact,
  RepoContext,
  RunStatus,
  StreamEvent,
} from "../lib/types";

interface RunState {
  runStatus: RunStatus;
  request: string;
  agentOrder: string[];
  agents: Record<string, AgentState>;
  artifactOrder: string[];
  artifacts: Record<string, Artifact>;
  loops: { iteration: number; comments: string[]; final?: boolean }[];
  repoContext: RepoContext | null;
  durationMs: number | null;
  providerLabel: string | null;
  activeAgent: string | null;
  error: string | null;
}

const initialRun: RunState = {
  runStatus: "idle",
  request: "",
  agentOrder: [],
  agents: {},
  artifactOrder: [],
  artifacts: {},
  loops: [],
  repoContext: null,
  durationMs: null,
  providerLabel: null,
  activeAgent: null,
  error: null,
};

export function useAgentStream() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [state, setState] = useState<RunState>(initialRun);
  const esRef = useRef<EventSource | null>(null);
  const finishedRef = useRef(false);

  // Load provider config once for the header badge.
  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => setConfig(null));
  }, []);

  const closeStream = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  const apply = useCallback((ev: StreamEvent) => {
    setState((s) => {
      switch (ev.type) {
        case "run_start":
          return { ...s, providerLabel: ev.provider_label };

        case "plan": {
          const agents: Record<string, AgentState> = {};
          const agentOrder: string[] = [];
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

        case "repo_context":
          return {
            ...s,
            repoContext: {
              repo: ev.repo,
              count: ev.count,
              files: ev.files ?? [],
              error: ev.error ?? null,
            },
          };

        case "agent_start": {
          const prev = s.agents[ev.agent];
          if (!prev) return s;
          return {
            ...s,
            activeAgent: ev.agent,
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
            agents: {
              ...s.agents,
              [ev.agent]: { ...prev, stream: prev.stream + ev.text },
            },
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
          let status: AgentState["status"] = "done";
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
                comments: ev.comments ?? [],
              },
            },
          };
        }

        case "loop":
          return {
            ...s,
            loops: [...s.loops, { iteration: ev.iteration, comments: ev.comments, final: ev.final }],
          };

        case "run_complete":

          return { ...s, runStatus: "done", durationMs: ev.duration_ms, activeAgent: null };

        case "error":
          return { ...s, error: ev.message };

        default:
          return s;
      }
    });
  }, []);

  const run = useCallback(
    (request: string, repo?: string) => {
      const trimmed = request.trim();
      if (!trimmed) return;
      closeStream();
      finishedRef.current = false;
      setState({ ...initialRun, runStatus: "running", request: trimmed });

      const qs = new URLSearchParams({ request: trimmed });
      if (repo?.includes("/")) qs.set("repo", repo.trim());
      const es = new EventSource(`/api/stream?${qs.toString()}`);
      esRef.current = es;
      es.onmessage = (e) => {
        let ev: StreamEvent;
        try {
          ev = JSON.parse(e.data) as StreamEvent;
        } catch {
          return; // ignore malformed frame
        }
        apply(ev);
        // Terminal events: the backend ends its generator right after these,
        // which closes the HTTP response. An EventSource AUTO-RECONNECTS when
        // the server closes the connection — silently re-issuing the same
        // GET /api/stream and re-running the entire pipeline, over and over
        // (the repeated /api/stream calls seen in the logs). Closing it here
        // ourselves is what actually stops that reconnect loop.
        if (ev.type === "run_complete" || ev.type === "error") {
          finishedRef.current = true;
          closeStream();
        }
      };
      es.onerror = () => {
        // On normal completion the terminal event already closed the stream.
        // If we somehow get here still "finished", close again so the browser
        // never auto-reconnects (which would re-run the whole pipeline).
        if (finishedRef.current) {
          closeStream();
          return;
        }
        closeStream();
        setState((s) => ({
          ...s,
          runStatus: s.runStatus === "running" ? "error" : s.runStatus,
          error: s.error ?? "Connection closed unexpectedly.",
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

