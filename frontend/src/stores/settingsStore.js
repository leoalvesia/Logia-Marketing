/**
 * Extended settings store — adds social accounts, monitored profiles,
 * brand identity and tone-of-voice to the existing nicho/persona fields.
 */
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { persist } from "zustand/middleware";
import { settingsApi } from "@/services/pipelineApi";

const DEFAULT_SOCIAL_ACCOUNTS = [
  { id: "instagram", name: "Instagram", token: null, status: "disconnected", expiresAt: null },
  { id: "linkedin", name: "LinkedIn", token: null, status: "disconnected", expiresAt: null },
  { id: "twitter", name: "Twitter/X", token: null, status: "disconnected", expiresAt: null },
  { id: "youtube", name: "YouTube", token: null, status: "disconnected", expiresAt: null },
  { id: "email", name: "E-mail (SMTP)", token: null, status: "disconnected", expiresAt: null },
];

// Profiles are fetched from the API — no hardcoded seed data.

const DEFAULT_BRAND = {
  primaryColor: "#6366F1",
  secondaryColor: "#10B981",
  logoDataUrl: null,
  fontFamily: "Inter",
};

const DEFAULT_PERSONA = {
  nicho: "",
  persona: "",
  keywords: [],
  tone: "professional", // professional | casual | technical | inspirational
};

export const useSettingsStore = create(
  persist(
    immer((set, get) => ({
      socialAccounts: DEFAULT_SOCIAL_ACCOUNTS,
      monitoredProfiles: [],
      brand: DEFAULT_BRAND,
      persona: DEFAULT_PERSONA,
      loading: false,
      profilesLoaded: false,

      // ── Social accounts ──────────────────────────────────────
      connectAccount: (id) =>
        set((s) => {
          const acc = s.socialAccounts.find((a) => a.id === id);
          if (!acc) return;
          // Simulate successful OAuth
          const expiresAt = new Date();
          expiresAt.setDate(expiresAt.getDate() + 60);
          acc.token = `mock-token-${id}`;
          acc.status = "connected";
          acc.expiresAt = expiresAt.toISOString();
        }),

      disconnectAccount: (id) =>
        set((s) => {
          const acc = s.socialAccounts.find((a) => a.id === id);
          if (!acc) return;
          acc.token = null;
          acc.status = "disconnected";
          acc.expiresAt = null;
        }),

      // ── Monitored profiles ───────────────────────────────────
      fetchProfiles: async () => {
        set((s) => { s.loading = true; });
        try {
          const data = await settingsApi.getProfiles();
          set((s) => {
            s.monitoredProfiles = data.profiles ?? [];
            s.profilesLoaded = true;
            s.loading = false;
          });
        } catch {
          set((s) => { s.loading = false; });
        }
      },

      addProfile: async (handle, platform) => {
        try {
          await settingsApi.addProfile(platform, handle);
          // Re-fetch to get server-assigned ID and created_at
          await get().fetchProfiles();
        } catch (e) {
          // Fallback: optimistic local add for offline/dev
          set((s) => {
            s.monitoredProfiles.push({
              id: `local-${Date.now()}`,
              handle: handle.replace(/^@/, ""),
              platform,
              active: true,
              created_at: new Date().toISOString(),
            });
          });
        }
      },

      removeProfile: async (id) => {
        set((s) => {
          s.monitoredProfiles = s.monitoredProfiles.filter((p) => p.id !== id);
        });
        try {
          await settingsApi.deleteProfile(id);
        } catch {
          // re-fetch to restore consistent state
          await get().fetchProfiles();
        }
      },

      toggleProfile: async (id) => {
        set((s) => {
          const p = s.monitoredProfiles.find((p) => p.id === id);
          if (p) p.active = !p.active;
        });
        try {
          await settingsApi.toggleProfile(id);
        } catch {
          await get().fetchProfiles();
        }
      },

      reorderProfiles: (from, to) =>
        set((s) => {
          const profiles = [...s.monitoredProfiles];
          const [moved] = profiles.splice(from, 1);
          profiles.splice(to, 0, moved);
          s.monitoredProfiles = profiles;
        }),

      // ── Brand identity ───────────────────────────────────────
      updateBrand: (updates) =>
        set((s) => {
          Object.assign(s.brand, updates);
        }),

      // ── Persona/niche ────────────────────────────────────────
      updatePersona: (updates) =>
        set((s) => {
          Object.assign(s.persona, updates);
        }),

      addKeyword: (kw) =>
        set((s) => {
          if (kw && !s.persona.keywords.includes(kw)) {
            s.persona.keywords.push(kw);
          }
        }),

      removeKeyword: (kw) =>
        set((s) => {
          s.persona.keywords = s.persona.keywords.filter((k) => k !== kw);
        }),

      setLoading: (loading) =>
        set((s) => { s.loading = loading; }),
    })),
    {
      name: "logia-settings-v2",
      partialize: (s) => ({
        socialAccounts: s.socialAccounts,
        monitoredProfiles: s.monitoredProfiles,
        brand: s.brand,
        persona: s.persona,
      }),
    }
  )
);
