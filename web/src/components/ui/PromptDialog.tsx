import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FileArchive } from "lucide-react";
import { usePromptState, resolvePrompt } from "../../store/prompt";

/**
 * Global text-prompt modal (a themed replacement for `window.prompt`). Mount
 * once at the app root. Enter submits, Esc / backdrop-click cancels.
 */
export default function PromptDialog() {
  const state = usePromptState();
  const open = !!state?.open;
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Seed the input each time a new prompt opens, then focus + select it.
  useEffect(() => {
    if (open && state) {
      setValue(state.defaultValue ?? "");
      const t = setTimeout(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      }, 30);
      return () => clearTimeout(t);
    }
  }, [open, state?.id]);

  const submit = () => resolvePrompt(value.trim());

  return (
    <AnimatePresence>
      {open && state && (
        <motion.div
          key="prompt-overlay"
          className="fixed inset-0 z-[100] grid place-items-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
        >
          <button
            aria-label="Cancel"
            onClick={() => resolvePrompt(null)}
            className="absolute inset-0 bg-ink-950/70 backdrop-blur-sm"
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            className="glass-strong relative w-full max-w-md rounded-card-lg p-5 shadow-soft"
            initial={{ opacity: 0, y: 14, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 14, scale: 0.96 }}
            transition={{ duration: 0.18 }}
          >
            <div className="flex items-start gap-3.5">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-accent-500/30 bg-accent-500/15 text-accent-300">
                <FileArchive className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                {state.title && (
                  <h2 className="text-base font-semibold text-slate-100">{state.title}</h2>
                )}
                {state.message && (
                  <p className="mt-0.5 text-sm leading-relaxed text-slate-300">{state.message}</p>
                )}
              </div>
            </div>

            <div className="mt-4 flex items-center gap-2 rounded-xl border border-white/10 bg-ink-900/60 px-3 focus-within:border-accent-500">
              <input
                ref={inputRef}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") submit();
                  else if (e.key === "Escape") resolvePrompt(null);
                }}
                placeholder={state.placeholder}
                spellCheck={false}
                className="min-w-0 flex-1 bg-transparent py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
              />
              {state.suffix && (
                <span className="shrink-0 font-mono text-xs text-slate-500">{state.suffix}</span>
              )}
            </div>

            <div className="mt-5 flex justify-end gap-2.5">
              <button className="btn btn-ghost !py-2" onClick={() => resolvePrompt(null)}>
                {state.cancelLabel ?? "Cancel"}
              </button>
              <button className="btn btn-primary !py-2" onClick={submit} disabled={!value.trim()}>
                {state.confirmLabel ?? "Download"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

