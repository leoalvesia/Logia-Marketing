/**
 * Extended settings store — adds social accounts, monitored profiles,
 * brand identity and tone-of-voice to the existing nicho/persona fields.
 */
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { persist } from "zustand/middleware";

const DEFAULT_SOCIAL_ACCOUNTS = [
  { id: "instagram", name: "Instagram", token: null, status: "disconnected", expiresAt: null },
  { id: "linkedin", name: "LinkedIn", token: null, status: "disconnected", expiresAt: null },
  { id: "twitter", name: "Twitter/X", token: null, status: "disconnected", expiresAt: null },
  { id: "youtube", name: "YouTube", token: null, status: "disconnected", expiresAt: null },
  { id: "email", name: "E-mail (SMTP)", token: null, status: "disconnected", expiresAt: null },
];

const DEFAULT_PROFILES = [
  { id: "p1", handle: "@resultadosdigitais", platform: "instagram", active: true, priority: 1 },
  { id: "p2", handle: "@neilpatel", platform: "instagram", active: true, priority: 2 },
  { id: "p3", handle: "resultadosdigitais", platform: "linkedin", active: false, priority: 3 },
  { id: "p4", handle: "@hubspotbr", platform: "twitter", active: true, priority: 4 },
];

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
      monitoredProfiles: DEFAULT_PROFILES,
      brand: DEFAULT_BRAND,
      persona: DEFAULT_PERSONA,
      loading: false,

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
      addProfile: (handle, platform) =>
        set((s) => {
          const id = `p${Date.now()}`;
          s.monitoredProfiles.push({
            id,
            handle,
            platform,
            active: true,
            priority: s.monitoredProfiles.length + 1,
          });
        }),

      removeProfile: (id) =>
        set((s) => {
          s.monitoredProfiles = s.monitoredProfiles.filter((p) => p.id !== id);
        }),

      toggleProfile: (id) =>
        set((s) => {
          const p = s.monitoredProfiles.find((p) => p.id === id);
          if (p) p.active = !p.active;
        }),

      reorderProfiles: (from, to) =>
        set((s) => {
          const profiles = [...s.monitoredProfiles];
          const [moved] = profiles.splice(from, 1);
          profiles.splice(to, 0, moved);
          profiles.forEach((p, i) => { p.priority = i + 1; });
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
