import { create } from "zustand";
import { immer } from "zustand/middleware/immer";

export const useLibraryStore = create(
  immer((set, get) => ({
    copies: [],
    arts: [],
    total: 0,
    page: 1,
    perPage: 20,
    hasNext: false,
    loading: false,
    filters: {
      channel: null,  // 'instagram' | 'linkedin' | ... | null
      status: null,   // 'draft' | 'approved' | 'published' | null
    },

    setLoading: (loading) =>
      set((s) => {
        s.loading = loading;
      }),

    setCopiesPage: ({ copies, total, page, per_page, has_next }) =>
      set((s) => {
        s.copies = copies;
        s.total = total;
        s.page = page;
        s.perPage = per_page;
        s.hasNext = has_next;
        s.loading = false;
      }),

    setArts: (arts) =>
      set((s) => {
        s.arts = arts;
      }),

    setFilter: (key, value) =>
      set((s) => {
        s.filters[key] = value;
        s.page = 1; // reset to first page on filter change
      }),

    setPage: (page) =>
      set((s) => {
        s.page = page;
      }),

    // Memoized selectors
    filteredCopies: () => {
      const { copies, filters } = get();
      return copies.filter((c) => {
        if (filters.channel && c.channel !== filters.channel) return false;
        if (filters.status && c.status !== filters.status) return false;
        return true;
      });
    },
  }))
);
