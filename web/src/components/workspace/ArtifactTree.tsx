import { useMemo, useState } from "react";
import {
  BookOpen,
  ChevronRight,
  FileCode2,
  FileText,
  FlaskConical,
  Folder,
  FolderOpen,
  Settings2,
} from "lucide-react";
import type { Artifact } from "../../lib/types";

interface Props {
  artifactOrder: string[];
  artifacts: Record<string, Artifact>;
  activeFile: string | null;
  onOpen: (name: string) => void;
  selected: Set<string>;
  onToggleSelect: (name: string) => void;
}

interface FileNode {
  type: "file";
  name: string;
  artifact: Artifact;
}
interface DirNode {
  type: "dir";
  name: string;
  path: string;
  children: TreeNode[];
}
type TreeNode = FileNode | DirNode;

function buildTree(order: string[], artifacts: Record<string, Artifact>): TreeNode[] {
  const root: DirNode = { type: "dir", name: "", path: "", children: [] };
  for (const fullName of order) {
    const art = artifacts[fullName];
    if (!art) continue;
    const parts = fullName.split("/");
    let cur = root;
    for (let i = 0; i < parts.length - 1; i++) {
      const seg = parts[i];
      let dir = cur.children.find((c) => c.type === "dir" && c.name === seg) as DirNode | undefined;
      if (!dir) {
        dir = { type: "dir", name: seg, path: cur.path ? `${cur.path}/${seg}` : seg, children: [] };
        cur.children.push(dir);
      }
      cur = dir;
    }
    cur.children.push({ type: "file", name: parts[parts.length - 1], artifact: art });
  }
  const sortRec = (d: DirNode) => {
    d.children.sort((a, b) => {
      if (a.type !== b.type) return a.type === "dir" ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    for (const c of d.children) if (c.type === "dir") sortRec(c);
  };
  sortRec(root);
  return root.children;
}

function fileIcon(type: string) {
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

/**
 * VS Code-style artifact tree (UI_SPEC §9). Derives nested folders from each
 * artifact's `name` path, supports collapse/expand, per-file selection
 * checkboxes (for GitHub publish), and click-to-open into the preview pane.
 */
export default function ArtifactTree({
  artifactOrder,
  artifacts,
  activeFile,
  onOpen,
  selected,
  onToggleSelect,
}: Readonly<Props>) {
  const tree = useMemo(
    () => buildTree(artifactOrder, artifacts),
    [artifactOrder, artifacts],
  );
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const toggleDir = (path: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });

  const renderNodes = (nodes: TreeNode[], depth: number): React.ReactNode =>
    nodes.map((node) => {
      const pad = { paddingLeft: `${depth * 14 + 8}px` };
      if (node.type === "dir") {
        const isOpen = !collapsed.has(node.path);
        return (
          <div key={"d:" + node.path}>
            <button
              onClick={() => toggleDir(node.path)}
              style={pad}
              className="flex w-full items-center gap-1.5 rounded-md py-1.5 pr-2 text-left text-[13px] text-slate-300 transition hover:bg-white/[0.05]"
            >
              <ChevronRight
                className={["h-3.5 w-3.5 shrink-0 transition", isOpen ? "rotate-90" : ""].join(" ")}
              />
              {isOpen ? (
                <FolderOpen className="h-4 w-4 shrink-0 text-amber-300/80" />
              ) : (
                <Folder className="h-4 w-4 shrink-0 text-amber-300/80" />
              )}
              <span className="truncate font-medium">{node.name}</span>
            </button>
            {isOpen && renderNodes(node.children, depth + 1)}
          </div>
        );
      }

      const a = node.artifact;
      const isActive = a.name === activeFile;
      const isSelected = selected.has(a.name);
      return (
        <div
          key={"f:" + a.name}
          style={pad}
          className={[
            "group flex items-center gap-2 rounded-md py-1.5 pr-2 text-[13px] transition",
            isActive ? "bg-brand-500/15 ring-1 ring-brand-500/40" : "hover:bg-white/[0.05]",
          ].join(" ")}
        >
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect(a.name)}
            onClick={(e) => e.stopPropagation()}
            title={isSelected ? "Selected for publish" : "Select for publish"}
            className="h-3.5 w-3.5 shrink-0 accent-indigo-500"
          />
          <button
            onClick={() => onOpen(a.name)}
            className="flex min-w-0 flex-1 items-center gap-2 text-left"
          >
            {fileIcon(a.type)}
            <span
              className={[
                "truncate font-mono text-[12.5px]",
                isActive ? "text-white" : "text-slate-300",
              ].join(" ")}
            >
              {node.name}
            </span>
            {isSelected && (
              <span className="ml-auto rounded border border-indigo-400/40 bg-indigo-400/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-indigo-200">
                selected
              </span>
            )}
          </button>
        </div>
      );
    });

  return <div className="py-1">{renderNodes(tree, 0)}</div>;
}

