import { motion } from "framer-motion";
import { Link } from "../lib/router";
import { ArrowRight, Github, Play, Sparkles } from "lucide-react";
import HeroTerminal from "../components/landing/HeroTerminal";
import FeatureGrid from "../components/landing/FeatureGrid";
import HowItWorks from "../components/landing/HowItWorks";
import MarketingFooter from "../components/landing/MarketingFooter";
import TopBar from "../components/shell/TopBar";

export default function Landing() {
  return (
    <div className="relative min-h-full overflow-hidden">

      {/* Nav */}
      <TopBar
        sticky={false}
        right={
          <>
            <Link
              to="/dashboard"
              className="hidden rounded-xl px-3 py-2 text-sm font-semibold text-slate-300 transition hover:text-white sm:inline-flex"
            >
              Dashboard
            </Link>
            <Link
              to="/app"
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-b from-accent to-accent-600 px-4 py-2 text-sm font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5"
            >
              Launch App <ArrowRight className="h-4 w-4" />
            </Link>
          </>
        }
      />

      {/* Hero */}
      <section className="relative z-10 mx-auto grid max-w-[1200px] items-center gap-10 px-6 pb-12 pt-10 lg:grid-cols-2 lg:pt-20">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs font-semibold text-accent-400">
            <Sparkles className="h-3.5 w-3.5" /> Autonomous multi-agent SDLC
          </span>
          <h1 className="mt-4 text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
            From idea to working code —{" "}
            <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
              in minutes.
            </span>
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-slate-400">
            A virtual software team that turns a one-line request into requirements, design,
            reviewed code, tests, and docs — then ships it as a GitHub PR.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link
              to="/app"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-b from-accent to-accent-600 px-5 py-3 text-sm font-semibold text-white shadow-glow-accent transition hover:-translate-y-0.5"
            >
              <Play className="h-4 w-4" /> Launch App
            </Link>
            <a
              href="https://github.com/amitsinghlabana"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-semibold text-slate-200 transition hover:bg-white/[0.08]"
            >
              <Github className="h-4 w-4" /> View on GitHub
            </a>
          </div>
          <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500">
            <span>✓ 6 specialized agents</span>
            <span>✓ Live streaming runs</span>
            <span>✓ Grounded by Foundry IQ</span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.97, y: 24 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
        >
          <HeroTerminal />
        </motion.div>
      </section>

      <HowItWorks />
      <FeatureGrid />

      {/* CTA */}
      <section className="relative z-10 mx-auto max-w-[1200px] px-6 pb-20">
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-accent/15 via-fuchsia-500/10 to-accent2/15 p-10 text-center backdrop-blur-xl">
          <h2 className="text-3xl font-extrabold tracking-tight">Ready to watch the team work?</h2>
          <p className="mx-auto mt-3 max-w-lg text-slate-300">
            Describe a feature and watch six agents design, build, review, and ship it live.
          </p>
          <Link
            to="/app"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-bold text-ink-950 transition hover:-translate-y-0.5"
          >
            Launch App <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}

