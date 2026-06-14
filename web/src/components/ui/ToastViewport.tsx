import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, X, XCircle } from "lucide-react";
import { useToasts, dismissToast, type ToastTone } from "../../store/toast";

const TONE: Record<ToastTone, { icon: typeof Info; cls: string }> = {
  info: { icon: Info, cls: "text-slate-200" },
  success: { icon: CheckCircle2, cls: "text-emerald-300" },
  error: { icon: XCircle, cls: "text-rose-300" },
};

/** Renders global toasts (bottom-center). Mount once at the app root. */
export default function ToastViewport() {
  const toasts = useToasts();
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-5 z-50 flex flex-col items-center gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => {
          const { icon: Icon, cls } = TONE[t.tone];
          return (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 12, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.97 }}
              transition={{ duration: 0.2 }}
              className="pointer-events-auto flex items-center gap-2.5 rounded-xl border border-white/10 bg-ink-800/90 px-4 py-2.5 text-sm text-slate-100 shadow-soft backdrop-blur-xl"
            >
              <Icon className={`h-4 w-4 shrink-0 ${cls}`} />
              <span>{t.message}</span>
              <button
                onClick={() => dismissToast(t.id)}
                className="ml-1 rounded p-0.5 text-slate-400 transition hover:text-slate-200"
                aria-label="Dismiss"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

