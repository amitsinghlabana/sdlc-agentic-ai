import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

/**
 * App-wide error boundary. Without this, a render error in any page would blank
 * the screen silently. Here we surface the message + a reload so failures are
 * visible and recoverable.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Surface to the console for debugging.
    console.error("UI crashed:", error, info);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="grid min-h-screen place-items-center px-6 text-center">
        <div className="max-w-md">
          <span className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl border border-rose-400/40 bg-rose-400/10 text-2xl">
            ⚠️
          </span>
          <h1 className="text-xl font-bold text-slate-100">Something went wrong</h1>
          <p className="mt-2 text-sm text-slate-400">
            The interface hit an unexpected error. Your run data is safe.
          </p>
          <pre className="mt-4 max-h-40 overflow-auto rounded-xl border border-white/10 bg-ink-950/60 p-3 text-left font-mono text-xs text-rose-300">
            {error.message}
          </pre>
          <div className="mt-5 flex justify-center gap-2">
            <button
              onClick={() => this.setState({ error: null })}
              className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/[0.08]"
            >
              Try again
            </button>
            <a
              href="/"
              className="rounded-xl bg-gradient-to-b from-accent-500 to-accent-600 px-4 py-2 text-sm font-semibold text-white transition hover:-translate-y-0.5"
            >
              Reload home
            </a>
          </div>
        </div>
      </div>
    );
  }
}

