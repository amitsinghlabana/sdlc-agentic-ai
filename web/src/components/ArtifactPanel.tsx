import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Check,
  Copy,
  Download,
  FileCode2,
  FileText,
  FlaskConical,
  Folder,
  Settings2,
} from "lucide-react";
import type { Artifact } from "../lib/types";
import CodeBlock from "./CodeBlock";

function typeIcon(type: string) {
  const cls = "h-4 w-4 shrink-0";
  switch (type) {
    case "code":
      return <FileCode2 className={cls + " text-brand-300"} />;
    case "test":
      return <FlaskConical className={cls + " text-emerald-300"} />;
    case "config":
      return <Settings2 className={cls + " text-amber-300"} />;
    case "doc":
      return <BookOpen className={cls + " text-violet-300"} />;
    default:
      return <FileText className={cls + " text-slate-300"} />;
  }
}

interface Props {
  artifactOrder: string[];
  artifacts: Record<string, Artifact>;
}

export default function ArtifactPanel({ artifactOrder, artifacts }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Auto-select the first artifact as soon as one arrives.
  useEffect(() => {
    if (!selected && artifactOrder.length > 0) setSelected(artifactOrder[0]);
    if (selected && !artifacts[selected] && artifactOrder.length > 0) {
      setSelected(artifactOrder[0]);
    }
  }, [artifactOrder, artifacts, selected]);

  const active = selected ? artifacts[selected] : undefined;
  const count = artifactOrder.length;

  const copy = () => {
    if (!active) return;
    navigator.clipboard.writeText(active.content).then(() => {
      setCopied(true);
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
  };

  const headerRight = useMemo(
    () => (
      <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-0.5 text-xs text-slate-300">
        {count} file{count === 1 ? "" : "s"}
      </span>
    ),
    [count]
  );

  return (
    <aside className="glass flex h-full flex-col overflow-hidden rounded-2xl shadow-soft">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <Folder className="h-4 w-4 text-slate-400" />
          <span className="label-caps">Artifacts</span>
        </div>
        {headerRight}
      </div>

      {count === 0 ? (
        <div className="grid flex-1 place-items-center p-10 text-center">
          <p className="text-sm text-slate-500">
            Generated files (specs, code, tests, docs) will appear here as the team works.
          </p>
        </div>
      ) : (
        <>
          {/* file list */}
          <ul className="max-h-44 overflow-auto border-b border-white/10 p-2">
            {artifactOrder.map((name) => {
              const a = artifacts[name];
              const isActive = name === selected;
              return (
                <li key={name}>
                  <button
                    onClick={() => setSelected(name)}
                    className={[
                      "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm transition-colors",
                      isActive
                        ? "bg-brand-500/15 text-white ring-1 ring-brand-500/40"
                        : "text-slate-300 hover:bg-white/[0.05]",
                    ].join(" ")}
                  >
                    {typeIcon(a.type)}
                    <span className="truncate font-mono text-[12.5px]">{name}</span>
                    <span className="ml-auto rounded border border-white/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-500">
                      {a.type}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {/* viewer */}
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
            <span className="truncate font-mono text-xs text-slate-400">
              {active ? `${active.name} · ${active.language}` : "Select a file"}
            </span>
            <div className="flex items-center gap-1.5">
              <button
                className="btn btn-ghost !px-2.5 !py-1.5 text-xs"
                onClick={copy}
                disabled={!active}
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
              <button
                className="btn btn-ghost !px-2.5 !py-1.5 text-xs"
                onClick={download}
                disabled={!active}
              >
                <Download className="h-3.5 w-3.5" />
                Save
              </button>
            </div>
          </div>

          <div className="min-h-[240px] flex-1 overflow-hidden bg-ink-950/40">
            {active && <CodeBlock content={active.content} language={active.language} />}
          </div>
        </>
      )}
    </aside>
  );
}

