import { Boxes } from "lucide-react";

export default function MarketingFooter() {
  return (
    <footer className="relative z-10 border-t border-white/10 bg-ink-950/40">
      <div className="mx-auto flex max-w-[1200px] flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
        <div className="flex items-center gap-2.5 text-slate-300">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-accent to-accent-600">
            <Boxes className="h-4 w-4 text-white" />
          </span>
          <span className="text-sm font-semibold">SDLC Agentic AI</span>
        </div>
        <p className="text-xs text-slate-500">
          Built for the hackathon · Powered by Azure OpenAI + Foundry IQ
        </p>
      </div>
    </footer>
  );
}

