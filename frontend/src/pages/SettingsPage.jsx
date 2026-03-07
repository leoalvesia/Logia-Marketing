import * as Tabs from "@radix-ui/react-tabs";
import { Link2, Users, Palette, Target } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import SocialAccountsTab from "@/components/Settings/SocialAccountsTab";
import MonitoredProfilesTab from "@/components/Settings/MonitoredProfilesTab";
import BrandIdentityTab from "@/components/Settings/BrandIdentityTab";
import PersonaTab from "@/components/Settings/PersonaTab";

const TABS = [
  { value: "social", label: "Contas Sociais", icon: Link2, component: SocialAccountsTab },
  { value: "profiles", label: "Perfis Monitorados", icon: Users, component: MonitoredProfilesTab },
  { value: "brand", label: "Identidade Visual", icon: Palette, component: BrandIdentityTab },
  { value: "persona", label: "Nicho / Persona", icon: Target, component: PersonaTab },
];

export default function SettingsPage() {
  const toast = useToast();

  function handleBrandSave() {
    toast({ type: "success", title: "Identidade visual salva", description: "Cores, logo e fonte atualizados." });
  }

  return (
    <main
      id="settings-main"
      className="p-5 md:p-6 max-w-3xl mx-auto space-y-6 animate-[fade-in_0.25s_ease-out]"
      aria-labelledby="settings-heading"
    >
      {/* Page header */}
      <div>
        <h1 id="settings-heading" className="text-xl font-bold text-[#F9FAFB]">Configurações</h1>
        <p className="text-xs text-[#6B7280] mt-0.5">Gerencie contas, perfis monitorados, identidade e persona</p>
      </div>

      {/* Tab navigation */}
      <Tabs.Root defaultValue="social">
        <Tabs.List
          aria-label="Seções de configuração"
          className="flex border-b border-[#2E2E2E] gap-0 mb-6 overflow-x-auto scrollbar-none"
        >
          {TABS.map(({ value, label, icon: Icon }) => (
            <Tabs.Trigger
              key={value}
              value={value}
              className="flex items-center gap-1.5 px-4 py-3 text-xs font-medium text-[#6B7280] border-b-2 border-transparent whitespace-nowrap
                         data-[state=active]:border-[#6366F1] data-[state=active]:text-[#F9FAFB]
                         hover:text-[#9CA3AF] transition-all
                         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366F1]/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0F0F0F]
                         -mb-px shrink-0"
            >
              <Icon size={13} aria-hidden="true" />
              {label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        {/* Tab panels */}
        {TABS.map(({ value, component: Component }) => (
          <Tabs.Content
            key={value}
            value={value}
            className="outline-none focus-visible:ring-2 focus-visible:ring-[#6366F1]/50 rounded-lg"
          >
            <Component onSave={handleBrandSave} />
          </Tabs.Content>
        ))}
      </Tabs.Root>
    </main>
  );
}
