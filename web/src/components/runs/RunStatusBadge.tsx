import type { RunRecord } from "../../store/useRunStore";

const META: Record<RunRecord["status"], { label: string; cls: string }> = {
  done: { label: "Done", cls: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300" },
  error: { label: "Error", cls: "border-rose-400/40 bg-rose-400/10 text-rose-300" },
  stopped: { label: "Stopped", cls: "border-amber-400/40 bg-amber-400/10 text-amber-300" },
};

export default function RunStatusBadge({ status }: Readonly<{ status: RunRecord["status"] }>) {
  const m = META[status];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${m.cls}`}
    >
      {m.label}
    </span>
  );
}

