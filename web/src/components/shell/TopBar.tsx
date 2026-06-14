import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Boxes } from "lucide-react";
import { Link } from "../../lib/router";

/**
 * The brand mark (logo + wordmark) shared by every page header so the product
 * identity is identical everywhere. Links back to the landing page.
 */
export function BrandMark({ subtitle }: Readonly<{ subtitle?: string }>) {
  return (
    <Link to="/" className="flex items-center gap-3">
      <motion.span
        initial={{ rotate: -8, scale: 0.9, opacity: 0 }}
        animate={{ rotate: 0, scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 14 }}
        className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-accent-500 to-accent-600 shadow-glow-accent"
      >
        <Boxes className="h-5 w-5 text-white" />
      </motion.span>
      <span className="leading-tight">
        <span className="block text-[15px] font-extrabold tracking-tight text-slate-50">
          SDLC Agentic AI
        </span>
        {subtitle && <span className="block text-[11px] text-slate-400">{subtitle}</span>}
      </span>
    </Link>
  );
}

interface TopBarProps {
  /** Page-specific actions rendered on the right side of the bar. */
  right?: ReactNode;
  /** Optional small caption under the wordmark. */
  subtitle?: string;
  /** Tailwind max-width class to match the page content width. */
  maxWidth?: string;
  /** Stick to the top while scrolling (off for the landing hero). */
  sticky?: boolean;
  /** Show the brand mark on the left. Off inside the app shell (Sidebar owns it). */
  showBrand?: boolean;
  /** Custom left content used when showBrand is false (e.g. a page title). */
  left?: ReactNode;
}

/**
 * Unified application header used across Landing, Dashboard, Runs and the
 * Workspace so the header looks and behaves the same on every page. The left
 * side is the shared <BrandMark /> (or a page title inside the app shell);
 * only the right-side actions differ.
 */
export default function TopBar({
  right,
  subtitle,
  maxWidth = "max-w-[1200px]",
  sticky = true,
  showBrand = true,
  left,
}: Readonly<TopBarProps>) {
  return (
    <header
      className={[
        sticky ? "sticky top-0 z-20" : "relative z-10",
        "border-b border-white/10 bg-ink-950/70 backdrop-blur-xl",
      ].join(" ")}
    >
      <div
        className={`mx-auto flex ${maxWidth} items-center justify-between gap-4 px-6 py-3`}
      >
        {showBrand ? <BrandMark subtitle={subtitle} /> : <div className="min-w-0">{left}</div>}
        {right && <div className="flex items-center gap-2.5">{right}</div>}
      </div>
    </header>
  );
}

