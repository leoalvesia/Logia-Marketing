import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { libraryApi } from "@/services/pipelineApi";

export const useLibraryStore = create(
  immer((set, get) => ({
    copies: [],
    arts: [],
    posts: [],
    total: 0,
    artsTotal: 0,
    postsTotal: 0,
    page: 1,
    perPage: 20,
    hasNext: false,
    loading: false,
    error: null,
    filters: {
      channel: null,
      status: null,
    },

    setFilter: (key, value) =>
      set((s) => {
        s.filters[key] = value;
        s.page = 1;
      }),

    setPage: (page) =>
      set((s) => {
        s.page = page;
      }),

    // ── Copies ────────────────────────────────────────────────
    fetchCopies: async ({ channel, status, page } = {}) => {
      set((s) => { s.loading = true; s.error = null; });
      try {
        const data = await libraryApi.getCopies({ channel, status, page });
        set((s) => {
          s.copies = data.copies;
          s.total = data.total;
          s.page = data.page;
          s.perPage = data.per_page;
          s.hasNext = data.has_next;
          s.loading = false;
        });
      } catch (e) {
        set((s) => { s.loading = false; s.error = e.message; });
      }
    },

    approveCopy: async (copyId) => {
      await libraryApi.approveCopy(copyId);
      // Re-fetch current page to reflect status change
      const { filters, page } = get();
      await get().fetchCopies({ ...filters, page });
    },

    deleteCopy: async (copyId) => {
      await libraryApi.deleteCopy(copyId);
      const { filters, page } = get();
      await get().fetchCopies({ ...filters, page });
    },

    // ── Arts ──────────────────────────────────────────────────
    fetchArts: async ({ type, page = 1 } = {}) => {
      set((s) => { s.loading = true; s.error = null; });
      try {
        const data = await libraryApi.getArts({ type, page });
        set((s) => {
          s.arts = data.arts;
          s.artsTotal = data.total;
          s.loading = false;
        });
      } catch (e) {
        set((s) => { s.loading = false; s.error = e.message; });
      }
    },

    // ── Posts ─────────────────────────────────────────────────
    fetchPosts: async ({ page = 1 } = {}) => {
      set((s) => { s.loading = true; s.error = null; });
      try {
        const data = await libraryApi.getPosts({ page });
        set((s) => {
          s.posts = data.posts;
          s.postsTotal = data.total;
          s.loading = false;
        });
      } catch (e) {
        set((s) => { s.loading = false; s.error = e.message; });
      }
    },
  }))
);
