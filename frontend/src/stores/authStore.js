import { create } from "zustand";
import { persist } from "zustand/middleware";
import * as Sentry from "@sentry/react";

/**
 * Auth store com persistência em localStorage.
 * user: { id, name, email }
 */
export const useAuthStore = create(
    persist(
        (set, get) => ({
            user: null,
            token: null,

            get isAuthenticated() {
                return !!get().token;
            },

            login: (user, token) => {
                // Sentry user context — apenas ID (sem PII além do identificador)
                if (user?.id) {
                    Sentry.setUser({ id: String(user.id) });
                }
                set({ user, token });
            },

            logout: () => {
                Sentry.setUser(null);
                set({ user: null, token: null });
            },

            completeOnboarding: () => {
                set((state) => ({
                    user: state.user ? { ...state.user, onboarding_completed: true } : state.user,
                }));
            },
        }),
        {
            name: "logia-auth",
            partialize: (s) => ({ user: s.user, token: s.token }),
        }
    )
);
