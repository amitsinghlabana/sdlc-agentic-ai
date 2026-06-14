import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Command,
  Home,
  LayoutDashboard,
  ListChecks,
  Play,
  Search,
  Github,
  CornerDownLeft,
} from "lucide-react";
import { useRouter } from "../../lib/router";

interface Cmd {
  id: string;
  label: string;
  hint: string;
  icon: typeof Home;
  keywords: string;
  run: (nav: (to: string) => void) => void;
}

const COMMANDS: Cmd[] = [
  { id: "home", label: "Go to Landing", hint: "/", icon: Home, keywords: "home landing marketing start", run: (n) => n("/") },
  { id: "dash", label: "Go to Dashboard", hint: "/dashboard", icon: LayoutDashboard, keywords: "dashboard overview stats home", run: (n) => n("/dashboard") },
  { id: "runs", label: "View Runs History", hint: "/runs", icon: ListChecks, keywords: "runs history past log table", run: (n) => n("/runs") },
  { id: "new", label: "New Run", hint: "/app", icon: Play, keywords: "new run start workspace compose feature build", run: (n) => n("/app") },
  {
    id: "gh",
    label: "Open GitHub",
    hint: "external",
    icon: Github,
    keywords: "github repo source code",
    run: () => globalThis.open("https://github.com/amitsinghlabana", "_blank"),
  },
];

/** Global Cmd/Ctrl+K command palette. Mount once at the app root. */
export default function CommandPalette() {
  const { navigate } = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global hotkey + close on Escape.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    };
    const onOpen = () => setOpen(true);
    globalThis.addEventListener("keydown", onKey);
    globalThis.addEventListener("sdlc:cmdk", onOpen);
    return () => {
      globalThis.removeEventListener("keydown", onKey);
      globalThis.removeEventListener("sdlc:cmdk", onOpen);
    };
  }, []);

  // Reset + focus when opened.
  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      const t = globalThis.setTimeout(() => inputRef.current?.focus(), 30);
      return () => globalThis.clearTimeout(t);
    }
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return COMMANDS;
    return COMMANDS.filter(
      (c) => c.label.toLowerCase().includes(q) || c.keywords.includes(q),
    );
  }, [query]);

  useEffect(() => {
    setActive((a) => Math.min(a, Math.max(results.length - 1, 0)));
  }, [results.length]);

  const choose = (cmd?: Cmd) => {
    if (!cmd) return;
    setOpen(false);
    cmd.run(navigate);
  };

  const onListKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (a + 1) % Math.max(results.length, 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => (a - 1 + results.length) % Math.max(results.length, 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(results[active]);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12 }}
          className="fixed inset-0 z-[60] flex items-start justify-center bg-black/50 px-4 pt-[14vh] backdrop-blur-sm"
          onMouseDown={() => setOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.14 }}
            className="w-full max-w-[560px] overflow-hidden rounded-2xl border border-white/10 bg-ink-900/95 shadow-soft backdrop-blur-xl"
            onMouseDown={(e) => e.stopPropagation()}
            onKeyDown={onListKey}
          >
            <div className="flex items-center gap-2.5 border-b border-white/10 px-4 py-3">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type a command or search…"
                className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
              />
              <span className="flex items-center gap-1 rounded-md border border-white/10 px-1.5 py-0.5 text-[10px] text-slate-500">
                <Command className="h-3 w-3" />K
              </span>
            </div>

            <ul className="max-h-[320px] overflow-auto p-2">
              {results.length === 0 ? (
                <li className="px-3 py-6 text-center text-sm text-slate-500">No matches.</li>
              ) : (
                results.map((c, i) => {
                  const isActive = i === active;
                  const Icon = c.icon;
                  return (
                    <li key={c.id}>
                      <button
                        onMouseEnter={() => setActive(i)}
                        onClick={() => choose(c)}
                        className={[
                          "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition",
                          isActive ? "bg-accent-500/15 text-white" : "text-slate-300 hover:bg-white/[0.05]",
                        ].join(" ")}
                      >
                        <Icon className={`h-4 w-4 ${isActive ? "text-accent-400" : "text-slate-400"}`} />
                        <span className="flex-1">{c.label}</span>
                        <span className="font-mono text-[11px] text-slate-500">{c.hint}</span>
                        {isActive && <CornerDownLeft className="h-3.5 w-3.5 text-slate-500" />}
                      </button>
                    </li>
                  );
                })
              )}
            </ul>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}


