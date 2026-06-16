import type { ReactNode } from "react";
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
import ConfirmDialog from "./components/ui/ConfirmDialog";
import PromptDialog from "./components/ui/PromptDialog";
import Spotlight from "./components/landing/Spotlight";


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
      {/* Shared ambient background — identical on every page (landing + app). */}
      <Spotlight />
      {/* Instant content swap (SPA feel) — no route transition animation. */}
      <div key={key} className="relative z-10 min-h-full">
        {el}
      </div>
      {/* Global overlays — persist across route changes */}
      <CommandPalette />
      <ToastViewport />
      <ConfirmDialog />
      <PromptDialog />
    </>
  );
}

