import { motion } from "framer-motion";
import { Rocket } from "lucide-react";
import { Link } from "../../lib/router";

interface Props {
  title: string;
  body: string;
  cta?: { to: string; label: string };
}

export default function EmptyState({ title, body, cta }: Readonly<Props>) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="grid place-items-center rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-12 text-center"
    >
      <span className="mb-4 grid h-14 w-14 place-items-center rounded-2xl border border-accent/30 bg-accent/10">
        <Rocket className="h-6 w-6 text-accent-400" />
      </span>
      <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-slate-400">{body}</p>
      {cta && (
        <Link
          to={cta.to}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-gradient-to-b from-accent-500 to-accent-600 px-5 py-2.5 text-sm font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5"
        >
          {cta.label}
        </Link>
      )}
    </motion.div>
  );
}

