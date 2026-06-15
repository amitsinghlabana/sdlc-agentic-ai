import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  label: string;
  value: string;
  hint?: string;
  accent?: string;
}

export default function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  accent = "text-accent-400",
}: Readonly<Props>) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl transition hover:border-white/20">
      <div className="flex items-center justify-between">
        <span className="label-caps">{label}</span>
        <Icon className={`h-4 w-4 ${accent}`} />
      </div>
      <p className="mt-3 text-3xl font-extrabold tracking-tight text-slate-50">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

