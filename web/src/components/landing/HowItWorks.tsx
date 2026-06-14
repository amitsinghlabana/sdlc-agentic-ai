import { motion } from "framer-motion";

const STEPS = [
  { emoji: "🧭", name: "Requirements", desc: "Turns your idea into testable stories & acceptance criteria." },
  { emoji: "🏗", name: "Architect", desc: "Picks a pragmatic stack and defines the API contract." },
  { emoji: "💻", name: "Developer", desc: "Writes the code and tests — editing real files when given a repo." },
  { emoji: "🧪", name: "Tester", desc: "Adds unit tests and exercises the acceptance criteria." },
  { emoji: "🔎", name: "Reviewer", desc: "Security & quality pass; loops back for revisions." },
  { emoji: "📝", name: "Docs", desc: "Writes the README and run instructions." },
];

export default function HowItWorks() {
  return (
    <section className="relative z-10 mx-auto max-w-[1200px] px-6 py-20">
      <div className="mx-auto mb-12 max-w-2xl text-center">
        <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">How it works</h2>
        <p className="mt-3 text-slate-400">
          Six specialized agents hand off like a real team — with a review loop.
        </p>
      </div>

      <div className="relative grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map((s, i) => (
          <motion.div
            key={s.name}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.4, delay: (i % 3) * 0.1 }}
            className="relative rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl"
          >
            <div className="flex items-center gap-3">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-xl">
                {s.emoji}
              </span>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-accent-400">
                  Step {i + 1}
                </p>
                <h3 className="font-semibold text-slate-100">{s.name}</h3>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-slate-400">{s.desc}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

