import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface Line {
  who: string;
  text: string;
  tone: "agent" | "ok" | "muted" | "accent";
}

// A believable run transcript — mirrors the real 6-agent pipeline.
const SCRIPT: Line[] = [
  { who: "you", text: "Add email/password login to my web app", tone: "accent" },
  { who: "🧭 Requirements", text: "drafting user stories + acceptance criteria…", tone: "agent" },
  { who: "🧭 Requirements", text: "✓ 4 stories, 9 criteria — grounded via Foundry IQ", tone: "ok" },
  { who: "🏗 Architect", text: "choosing stack: FastAPI + JWT + bcrypt…", tone: "agent" },
  { who: "🏗 Architect", text: "✓ design.md + API contract", tone: "ok" },
  { who: "💻 Developer", text: "writing app/auth.py, routes, tests…", tone: "agent" },
  { who: "🔎 Reviewer", text: "security pass — flagging plaintext compare…", tone: "agent" },
  { who: "💻 Developer", text: "↻ revision 1 — bcrypt hashing applied", tone: "muted" },
  { who: "🔎 Reviewer", text: "✓ approved", tone: "ok" },
  { who: "📝 Docs", text: "✓ README + run instructions", tone: "ok" },
  { who: "✅ done", text: "6 artifacts ready · opened PR #1", tone: "accent" },
];

const TONE: Record<Line["tone"], string> = {
  agent: "text-slate-300",
  ok: "text-emerald-300",
  muted: "text-amber-300",
  accent: "text-violet-300",
};

export default function HeroTerminal() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (count >= SCRIPT.length) {
      const reset = setTimeout(() => setCount(0), 2600);
      return () => clearTimeout(reset);
    }
    const t = setTimeout(() => setCount((c) => c + 1), count === 0 ? 500 : 720);
    return () => clearTimeout(t);
  }, [count]);

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-ink-950/80 shadow-glow-accent backdrop-blur-xl">
      <div className="flex items-center gap-2 border-b border-white/10 bg-white/[0.03] px-4 py-2.5">
        <span className="h-3 w-3 rounded-full bg-rose-400/80" />
        <span className="h-3 w-3 rounded-full bg-amber-400/80" />
        <span className="h-3 w-3 rounded-full bg-emerald-400/80" />
        <span className="ml-2 font-mono text-xs text-slate-500">sdlc-agent · live run</span>
      </div>
      <div className="h-[320px] space-y-2 overflow-hidden p-4 font-mono text-[13px] leading-relaxed">
        {SCRIPT.slice(0, count).map((line, i) => (
          <motion.div
            key={`${line.who}-${i}`}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
            className="flex gap-2"
          >
            <span className="shrink-0 text-slate-500">{line.who}</span>
            <span className={TONE[line.tone]}>{line.text}</span>
          </motion.div>
        ))}
        {count < SCRIPT.length && (
          <span className="inline-block h-4 w-2 animate-pulse bg-violet-400/80 align-middle" />
        )}
      </div>
    </div>
  );
}

