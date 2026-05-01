import { create } from "zustand";

export type ThemeMode = "light" | "dark" | "system";

const STORAGE_KEY = "jaikalki:theme";

function readStoredMode(): ThemeMode {
  if (typeof window === "undefined") return "system";
  const stored = window.localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
  return stored ?? "system";
}

function resolveEffective(mode: ThemeMode): "light" | "dark" {
  if (mode !== "system") return mode;
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyDocumentClass(effective: "light" | "dark") {
  const root = document.documentElement;
  root.classList.toggle("dark", effective === "dark");
}

interface ThemeState {
  mode: ThemeMode;
  effective: "light" | "dark";
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
  init: () => void;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: readStoredMode(),
  effective: resolveEffective(readStoredMode()),

  setMode: (mode) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, mode);
    }
    const effective = resolveEffective(mode);
    applyDocumentClass(effective);
    set({ mode, effective });
  },

  toggle: () => {
    const { effective } = get();
    get().setMode(effective === "dark" ? "light" : "dark");
  },

  init: () => {
    const { mode } = get();
    const effective = resolveEffective(mode);
    applyDocumentClass(effective);
    set({ effective });
    if (typeof window !== "undefined") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const listener = () => {
        if (get().mode === "system") {
          const eff = resolveEffective("system");
          applyDocumentClass(eff);
          set({ effective: eff });
        }
      };
      mq.addEventListener("change", listener);
    }
  },
}));
