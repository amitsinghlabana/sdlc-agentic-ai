import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, HelpCircle } from "lucide-react";
import { useConfirmState, resolveConfirm } from "../../store/confirm";

/**
 * Global confirm modal (replaces `window.confirm`). Mount once at the app root.
 * Enter confirms, Esc / backdrop-click cancels. Styled to match the app theme.
 */
export default function ConfirmDialog() {
  const state = useConfirmState();
  const open = !!state?.open;

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") resolveConfirm(false);
      else if (e.key === "Enter") resolveConfirm(true);
    };
    globalThis.addEventListener("keydown", onKey);
    return () => globalThis.removeEventListener("keydown", onKey);
  }, [open]);

  const danger = state?.tone === "danger";
  const Icon = danger ? AlertTriangle : HelpCircle;

  return (
    <AnimatePresence>
      {open && state && (
        <motion.div
          key="confirm-overlay"
          className="fixed inset-0 z-[100] grid place-items-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
        >
          <button
            aria-label="Cancel"
            onClick={() => resolveConfirm(false)}
            className="absolute inset-0 bg-ink-950/70 backdrop-blur-sm"
          />
          <motion.div
            role="alertdialog"
            aria-modal="true"
            className="glass-strong relative w-full max-w-md rounded-card-lg p-5 shadow-soft"
            initial={{ opacity: 0, y: 14, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 14, scale: 0.96 }}
            transition={{ duration: 0.18 }}
          >
            <div className="flex items-start gap-3.5">
              <span
                className={[
                  "grid h-10 w-10 shrink-0 place-items-center rounded-xl border",
                  danger
                    ? "border-rose-400/30 bg-rose-500/15 text-rose-300"
                    : "border-accent-500/30 bg-accent-500/15 text-accent-300",
                ].join(" ")}
              >
                <Icon className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                {state.title && (
                  <h2 className="text-base font-semibold text-slate-100">{state.title}</h2>
                )}
                <p className="mt-0.5 text-sm leading-relaxed text-slate-300">{state.message}</p>
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-2.5">
              <button className="btn btn-ghost !py-2" onClick={() => resolveConfirm(false)}>
                {state.cancelLabel ?? "Cancel"}
              </button>
              <button
                autoFocus
                className={[
                  "btn !py-2 text-white",
                  danger
                    ? "bg-gradient-to-b from-rose-500 to-rose-600 shadow-soft hover:-translate-y-0.5"
                    : "btn-primary",
                ].join(" ")}
                onClick={() => resolveConfirm(true)}
              >
                {state.confirmLabel ?? "Confirm"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}


