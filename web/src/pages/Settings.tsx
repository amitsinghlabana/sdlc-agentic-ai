import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import {
  SlidersHorizontal,
  Server,
  KeyRound,
  Plug,
  Users,
  CreditCard,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import TopBar from "../components/shell/TopBar";
import ProviderSettingForm from "../components/settings/ProviderSettingForm";
import { useAdmin } from "../hooks/useAdmin";
import { toast } from "../store/toast";

type TabKey = "general" | "providers" | "keys" | "integrations" | "team" | "billing";

const TABS: { key: TabKey; label: string; icon: LucideIcon }[] = [
  { key: "general", label: "General", icon: SlidersHorizontal },
  { key: "providers", label: "Providers", icon: Server },
  { key: "keys", label: "API Keys", icon: KeyRound },
  { key: "integrations", label: "Integrations", icon: Plug },
  { key: "team", label: "Team", icon: Users },
  { key: "billing", label: "Billing", icon: CreditCard },
];

function Placeholder({ title, body }: Readonly<{ title: string; body: string }>) {
  return (
    <div className="grid place-items-center rounded-card border border-dashed border-white/10 bg-white/[0.02] p-12 text-center">
      <p className="text-sm font-semibold text-slate-300">{title}</p>
      <p className="mt-1 max-w-sm text-xs text-slate-500">{body}</p>
    </div>
  );
}

/**
 * Settings page (UI_VISUAL_SPEC Screen 05). Inner sidebar of sections with the
 * Providers tab wired to the live useAdmin hook; the remaining tabs are honest
 * placeholders until their backend endpoints exist.
 */
export default function Settings() {
  const [tab, setTab] = useState<TabKey>("providers");
  const notify = useCallback((msg: string) => toast(msg), []);
  const admin = useAdmin(notify);

  return (
    <div className="relative min-h-full">
      <TopBar
        maxWidth="max-w-[1100px]"
        showBrand={false}
        left={<span className="text-sm font-semibold text-slate-200">Settings</span>}
      />

      <main className="mx-auto max-w-[1100px] px-6 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-extrabold tracking-tight">Settings</h1>
          <p className="mt-1 text-slate-400">Configure your AI providers and integrations.</p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-[200px_1fr]">
          {/* Inner nav */}
          <nav className="flex gap-1 overflow-x-auto md:flex-col md:overflow-visible">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={[
                  "inline-flex items-center gap-2.5 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-medium transition",
                  tab === t.key
                    ? "bg-accent-500/15 text-accent-200 ring-1 ring-inset ring-accent-500/30"
                    : "text-slate-400 hover:bg-white/[0.05] hover:text-slate-100",
                ].join(" ")}
              >
                <t.icon className="h-4 w-4" />
                {t.label}
              </button>
            ))}
          </nav>

          {/* Panel */}
          <motion.section
            key={tab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {tab === "providers" && (
              <>
                <div className="mb-4">
                  <h2 className="text-lg font-bold text-slate-100">Providers</h2>
                  <p className="text-sm text-slate-400">
                    Switch any integration between mock and live without a restart. Choices persist;
                    live falls back to mock if not configured.
                  </p>
                </div>
                <ProviderSettingForm admin={admin} />
              </>
            )}
            {tab === "general" && (
              <Placeholder
                title="General settings"
                body="Workspace name, default branch and run preferences will live here."
              />
            )}
            {tab === "keys" && (
              <Placeholder
                title="API keys"
                body="Manage personal access tokens for the SDLC Agentic AI API."
              />
            )}
            {tab === "integrations" && (
              <Placeholder
                title="Integrations"
                body="Connect GitHub, JIRA and Foundry IQ. Configure them under Providers for now."
              />
            )}
            {tab === "team" && (
              <Placeholder
                title="Team members"
                body="Invite teammates and manage roles once authentication is enabled."
              />
            )}
            {tab === "billing" && (
              <Placeholder
                title="Billing"
                body="Usage-based billing and plan management — coming soon."
              />
            )}
          </motion.section>
        </div>
      </main>
    </div>
  );
}

