import type { ReactNode } from "react";
import Sidebar from "./Sidebar";

/**
 * The authenticated app shell: a persistent left <Sidebar /> plus a fluid
 * content column. Landing and the full-bleed Workspace opt out; Dashboard,
 * Runs and Settings render inside it (see App.tsx → pageFor).
 */
export default function AppShell({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <div className="flex min-h-full">
      <Sidebar />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

