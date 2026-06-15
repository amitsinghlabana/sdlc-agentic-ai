import { useEffect, useMemo, useState } from "react";
import {
  Check,
  ChevronsDownUp,
  ChevronsUpDown,
  Copy,
  Download,
  FileArchive,
  FolderTree,
  SquareCheck,
} from "lucide-react";
import type { Artifact } from "../../lib/types";
import CodeBlock from "../CodeBlock";
import ArtifactTree, { collectDirPaths } from "./ArtifactTree";
import { downloadZip } from "../../lib/zip";

interface Props {
  artifactOrder: string[];
  artifacts: Record<string, Artifact>;
  selected: Set<string>;
  onToggleSelect: (name: string) => void;
  onSelectAll: () => void;
}

const TOOLBAR_BTN =
  "inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] font-semibold text-slate-300 transition hover:bg-white/[0.07]";

/** Header actions: collapse/expand all, download zip, select/clear all. */
function ExplorerToolbar({
  allCollapsed,
  selectedAll,
  onToggleAll,
  onDownloadZip,
  onSelectAll,
}: Readonly<{
  allCollapsed: boolean;
  selectedAll: boolean;
  onToggleAll: () => void;
  onDownloadZip: () => void;
  onSelectAll: () => void;
}>) {
  return (
    <div className="flex items-center gap-1.5">
      <button
        onClick={onToggleAll}
        title={allCollapsed ? "Expand all folders" : "Collapse all folders"}
        className={TOOLBAR_BTN}
      >
        {allCollapsed ? (
          <ChevronsUpDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronsDownUp className="h-3.5 w-3.5" />
        )}
        {allCollapsed ? "Expand" : "Collapse"}
      </button>
      <button onClick={onDownloadZip} title="Download all artifacts as a .zip" className={TOOLBAR_BTN}>
        <FileArchive className="h-3.5 w-3.5" />
        Zip
      </button>
      <button onClick={onSelectAll} title="Select / clear all for publish" className={TOOLBAR_BTN}>
        <SquareCheck className="h-3.5 w-3.5" />
        {selectedAll ? "Clear" : "All"}
      </button>
    </div>
  );
}

/**
 * Right-hand artifacts panel (UI_SPEC §9–10): a VS Code-style file tree on top
 * and a syntax-highlighted preview below, with copy/download/select actions and
 * a sticky status footer. Selection drives the GitHub publish flow.
 */
export default function ArtifactExplorer({
  artifactOrder,
  artifacts,
  selected,
  onToggleSelect,
  onSelectAll,
}: Readonly<Props>) {
  const [active, setActive] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const allDirs = useMemo(() => collectDirPaths(artifactOrder), [artifactOrder]);
  const allCollapsed = allDirs.length > 0 && allDirs.every((d) => collapsed.has(d));

  const toggleDir = (path: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });

  const toggleAll = () => setCollapsed(allCollapsed ? new Set() : new Set(allDirs));

  const downloadAllZip = () => {
    const entries = artifactOrder
      .map((n) => artifacts[n])
      .filter(Boolean)
      .map((a) => ({ name: a.name, content: a.content }));
    if (entries.length > 0) downloadZip(entries, "sdlc-artifacts.zip");
  };

  useEffect(() => {
    if (!active && artifactOrder.length > 0) setActive(artifactOrder[0]);
    if (active && !artifacts[active] && artifactOrder.length > 0) setActive(artifactOrder[0]);
  }, [artifactOrder, artifacts, active]);

  const file = active ? artifacts[active] : undefined;
  const count = artifactOrder.length;

  const copy = () => {
    if (!file) return;
    navigator.clipboard.writeText(file.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    });
  };

  const download = () => {
    if (!file) return;
    const blob = new Blob([file.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = file.name.split("/").pop() || "artifact.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <aside className="glass flex h-full min-h-0 flex-col overflow-hidden rounded-card shadow-soft">
      {/* Explorer header */}
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-2.5">
        <div className="flex items-center gap-2">
          <FolderTree className="h-4 w-4 text-slate-400" />
          <span className="label-caps">Explorer</span>
          <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] text-slate-400">
            {count} file{count === 1 ? "" : "s"}
          </span>
        </div>
        {count > 0 && (
          <ExplorerToolbar
            allCollapsed={allCollapsed}
            selectedAll={selected.size === count}
            onToggleAll={toggleAll}
            onDownloadZip={downloadAllZip}
            onSelectAll={onSelectAll}
          />
        )}
      </div>

      {count === 0 ? (
        <div className="grid flex-1 place-items-center p-8 text-center">
          <p className="text-sm text-slate-500">
            Generated files (specs, code, tests, docs) appear here as the team works.
          </p>
        </div>
      ) : (
        <>
          {/* File tree */}
          <div className="max-h-[42%] min-h-[120px] overflow-auto border-b border-white/10">
            <ArtifactTree
              artifactOrder={artifactOrder}
              artifacts={artifacts}
              activeFile={active}
              onOpen={setActive}
              selected={selected}
              onToggleSelect={onToggleSelect}
              collapsed={collapsed}
              onToggleDir={toggleDir}
            />
          </div>

          {/* Preview header */}
          <div className="flex items-center justify-between gap-2 border-b border-white/10 px-3 py-2">
            <span className="truncate font-mono text-xs text-slate-400">
              {file ? file.name : "Select a file"}
            </span>
            <div className="flex shrink-0 items-center gap-1.5">
              <button
                className="btn btn-ghost !px-2 !py-1 text-xs"
                onClick={copy}
                disabled={!file}
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
              <button
                className="btn btn-ghost !px-2 !py-1 text-xs"
                onClick={download}
                disabled={!file}
              >
                <Download className="h-3.5 w-3.5" />
                Save
              </button>
              {file && (
                <button
                  className={[
                    "btn !px-2 !py-1 text-xs",
                    selected.has(file.name) ? "btn-primary" : "btn-ghost",
                  ].join(" ")}
                  onClick={() => onToggleSelect(file.name)}
                >
                  {selected.has(file.name) ? "Selected" : "Select"}
                </button>
              )}
            </div>
          </div>

          {/* Code preview */}
          <div className="min-h-0 flex-1 overflow-hidden bg-code/60">
            {file && <CodeBlock content={file.content} language={file.language} />}
          </div>

          {/* Status footer */}
          {file && (
            <div className="flex items-center gap-3 border-t border-white/10 px-3 py-1.5 font-mono text-[11px] text-slate-500">
              <span>Ln 1, Col 1</span>
              <span>UTF-8</span>
              <span className="capitalize text-slate-400">{file.language}</span>
              <span className="ml-auto">Spaces: 4</span>
            </div>
          )}
        </>
      )}
    </aside>
  );
}

