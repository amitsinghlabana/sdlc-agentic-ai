import { Link } from "../lib/router";
import { Boxes } from "lucide-react";

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center px-6 text-center">
      <div>
        <span className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-accent to-accent-600">
          <Boxes className="h-6 w-6 text-white" />
        </span>
        <h1 className="text-5xl font-extrabold tracking-tight">404</h1>
        <p className="mt-2 text-slate-400">This page wandered off the pipeline.</p>
        <Link
          to="/"
          className="mt-6 inline-flex rounded-xl border border-white/10 bg-white/[0.04] px-5 py-2.5 text-sm font-semibold text-slate-100 transition hover:bg-white/[0.08]"
        >
          Back home
        </Link>
      </div>
    </div>
  );
}

