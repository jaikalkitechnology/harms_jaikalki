import { create } from "zustand";

interface SidebarState {
  mobileOpen: boolean;
  collapsed: Record<string, boolean>;
  toggleMobile: () => void;
  closeMobile: () => void;
  toggleSection: (label: string) => void;
}

const STORAGE_KEY = "jaikalki:sidebar:collapsed";

function loadCollapsed(): Record<string, boolean> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "{}");
  } catch {
    return {};
  }
}

function persistCollapsed(state: Record<string, boolean>): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export const useSidebarStore = create<SidebarState>((set) => ({
  mobileOpen: false,
  collapsed: loadCollapsed(),
  toggleMobile: () => set((s) => ({ mobileOpen: !s.mobileOpen })),
  closeMobile: () => set({ mobileOpen: false }),
  toggleSection: (label) =>
    set((s) => {
      const next = { ...s.collapsed, [label]: !s.collapsed[label] };
      persistCollapsed(next);
      return { collapsed: next };
    }),
}));
