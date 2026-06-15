import type { LucideIcon } from "lucide-react";
import {
  Home,
  LayoutDashboard,
  Workflow,
  Zap,
  Settings,
  LifeBuoy,
  Boxes,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { Link, useRouter } from "../../lib/router";
import { BrandMark } from "./TopBar";
import { useSidebarCollapsed, toggleSidebar } from "../../store/useSidebar";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** Extra path prefixes that should also mark this item active. */
  match?: string[];
}

const NAV: NavItem[] = [
  { to: "/", label: "Home", icon: Home },
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { to: "/app", label: "Workspace", icon: Workflow },
  { to: "/runs", label: "Runs", icon: Zap },
  { to: "/settings/providers", label: "Settings", icon: Settings, match: ["/settings"] },
];


function isActive(path: string, item: NavItem): boolean {
  if (path === item.to) return true;
  return (item.match ?? []).some((m) => path.startsWith(m));
}

/**
 * Persistent left navigation shared by every in-app screen (Dashboard, Runs,
 * Settings AND the Workspace) so the side nav looks and behaves identically
 * everywhere. Brand at the top, primary nav with an accent-highlighted active
 * item, and a help link pinned to the bottom.
 */
export default function Sidebar() {
  const { path } = useRouter();
  const collapsed = useSidebarCollapsed();

  /** Shared row classes — icon-only + centered when collapsed. */
  const rowCls = (active: boolean) =>
    ["nav-link", collapsed ? "justify-center px-0" : "", active ? "nav-link-active" : ""]
      .filter(Boolean)
      .join(" ");

  return (
    <aside
      className={[
        "sticky top-0 hidden h-screen shrink-0 flex-col border-r border-white/10 bg-ink-950/60 backdrop-blur-xl transition-[width] duration-200 lg:flex",
        collapsed ? "w-16" : "w-64",
      ].join(" ")}
    >
      <div className={collapsed ? "flex justify-center px-2 py-4" : "px-5 py-4"}>
        {collapsed ? (
          <Link
            to="/"
            title="SDLC Agentic AI"
            className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-accent-500 to-accent-600 shadow-glow-accent"
          >
            <Boxes className="h-5 w-5 text-white" />
          </Link>
        ) : (
          <BrandMark />
        )}
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {!collapsed && <p className="px-3 pb-1 pt-2 label-caps">Workspace</p>}
        {NAV.map((item) => (
          <Link
            key={item.label}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={rowCls(isActive(path, item))}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed && item.label}
          </Link>
        ))}
      </nav>

      <div className="space-y-1 border-t border-white/10 p-3">
        <Link to="/" title={collapsed ? "Help & Docs" : undefined} className={rowCls(false)}>
          <LifeBuoy className="h-4 w-4 shrink-0" />
          {!collapsed && "Help & Docs"}
        </Link>
        <button
          type="button"
          onClick={toggleSidebar}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={[rowCls(false), "w-full text-left"].join(" ")}
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4 shrink-0" />
          ) : (
            <PanelLeftClose className="h-4 w-4 shrink-0" />
          )}
          {!collapsed && "Collapse"}
        </button>
      </div>
    </aside>
  );
}

