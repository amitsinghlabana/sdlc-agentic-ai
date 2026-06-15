import { useCallback, useState } from "react";
import { Server } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import TopBar from "../components/shell/TopBar";
import ProviderSettingForm from "../components/settings/ProviderSettingForm";
import { useAdmin } from "../hooks/useAdmin";
import { toast } from "../store/toast";

type TabKey = "providers";

const TABS: { key: TabKey; label: string; icon: LucideIcon }[] = [
  { key: "providers", label: "Integration", icon: Server },
];

/**
 * Settings page. A single Integration section wired to the live useAdmin hook,
 * letting you switch each provider (LLM, GitHub, JIRA, Foundry) between mock and
 * live without a restart.
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
          <section>
            {tab === "providers" && (
              <>
                <div className="mb-4">
                  <h2 className="text-lg font-bold text-slate-100">Integration</h2>
                  <p className="text-sm text-slate-400">
                    Switch any integration between mock and live without a restart. Choices persist;
                    live falls back to mock if not configured.
                  </p>
                </div>
                <ProviderSettingForm admin={admin} />
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

