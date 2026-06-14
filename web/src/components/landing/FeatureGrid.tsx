import { motion } from "framer-motion";
import { LockKeyhole, Users, Github, Activity, BookOpenCheck, GitPullRequest } from "lucide-react";

const FEATURES = [
  {
    Icon: LockKeyhole,
    title: "Requirement Lock",
    body: "Agents agree on testable user stories & acceptance criteria before a line of code is written.",
  },
  {
    Icon: Users,
    title: "Multi-Agent Team",
    body: "Requirements → Architect → Developer → Tester → Reviewer → Docs, collaborating live.",
  },
  {
    Icon: BookOpenCheck,
    title: "Grounded by Foundry IQ",
    body: "Retrieval-augmented standards keep output cited, consistent, and hallucination-resistant.",
  },
  {
    Icon: Github,
    title: "GitHub Integration",
    body: "Create a new repo or open a branch + PR on an existing one — with AI-authored commits.",
  },
  {
    Icon: Activity,
    title: "Live Streaming Runs",
    body: "Watch every agent think in real time over Server-Sent Events. No black boxes.",
  },
  {
    Icon: GitPullRequest,
    title: "JIRA Round-Trip",
    body: "Import an issue as a request, then push generated stories & sub-tasks straight back.",
  },
];

export default function FeatureGrid() {
  return (
    <section className="relative z-10 mx-auto max-w-[1200px] px-6 py-20">
      <div className="mx-auto mb-12 max-w-2xl text-center">
        <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
          Everything a software team does —{" "}
          <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
            automated
          </span>
        </h2>
        <p className="mt-3 text-slate-400">
          Not a single prompt-to-code toy. A full, reviewable SDLC pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.4, delay: (i % 3) * 0.1 }}
            className="group rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl transition hover:border-accent/40 hover:bg-white/[0.05]"
          >
            <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl border border-accent/30 bg-accent/10 text-accent-400 transition group-hover:scale-105">
              <f.Icon className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-100">{f.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-slate-400">{f.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

