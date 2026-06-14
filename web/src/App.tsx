import type { ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "./lib/router";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import RunsHistory from "./pages/RunsHistory";
import Workspace from "./pages/Workspace";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import AppShell from "./components/shell/AppShell";
import CommandPalette from "./components/shell/CommandPalette";
import ToastViewport from "./components/ui/ToastViewport";

/** Wrap a page in an enter/exit fade so route changes feel intentional. */
function Page({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.22 }}
      className="min-h-full"
    >
      {children}
    </motion.div>
  );
}

/** Pages that live inside the persistent sidebar shell. */
function shell(el: ReactNode) {
  return <AppShell>{el}</AppShell>;
}

function pageFor(path: string) {
  if (path === "/" || path === "") return { key: "landing", el: <Landing /> };
  if (path === "/dashboard" || path.startsWith("/dashboard"))
    return { key: "dashboard", el: shell(<Dashboard />) };
  if (path === "/runs" || path.startsWith("/runs"))
    return { key: "runs", el: shell(<RunsHistory />) };
  if (path === "/settings" || path.startsWith("/settings"))
    return { key: "settings", el: shell(<Settings />) };
  if (path === "/app" || path.startsWith("/app")) return { key: "app", el: <Workspace /> };
  return { key: "404", el: <NotFound /> };
}

export default function App() {
  const { path } = useRouter();
  const { key, el } = pageFor(path);
  return (
    <>
      <AnimatePresence mode="wait">
        <Page key={key}>{el}</Page>
      </AnimatePresence>
      {/* Global overlays — persist across route changes */}
      <CommandPalette />
      <ToastViewport />
    </>
  );
}

