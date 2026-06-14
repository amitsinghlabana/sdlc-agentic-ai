import type { LucideIcon } from "lucide-react";

export interface WorkspaceTab<K extends string> {
  key: K;
  label: string;
  icon: LucideIcon;
  /** Optional count badge (e.g. number of artifacts/tests). */
  count?: number;
}

interface Props<K extends string> {
  tabs: WorkspaceTab<K>[];
  active: K;
  onChange: (key: K) => void;
}

/**
 * Underline-style tab strip for the workspace right panel
 * (Artifacts | Tests | Diff). Matches UI_VISUAL_SPEC Screen 03 tab styling.
 */
export default function WorkspaceTabs<K extends string>({
  tabs,
  active,
  onChange,
}: Readonly<Props<K>>) {
  return (
    <div className="flex items-center gap-1 border-b border-white/10">
      {tabs.map((t) => {
        const isActive = t.key === active;
        return (
          <button
            key={t.key}
            onClick={() => onChange(t.key)}
            className={[
              "inline-flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition",
              isActive
                ? "border-accent-500 text-slate-100"
                : "border-transparent text-slate-400 hover:text-slate-200",
            ].join(" ")}
          >
            <t.icon className="h-3.5 w-3.5" />
            {t.label}
            {typeof t.count === "number" && (
              <span className="rounded-pill border border-white/10 bg-white/[0.04] px-1.5 text-[10px] text-slate-400">
                {t.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

