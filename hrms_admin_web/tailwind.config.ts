import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        // Jaikalki brand. Text + surface tokens point at CSS vars so
        // dark mode can flip them. Pure decorative shades (gold, etc.)
        // stay as static hex.
        brand: {
          brown: "#3D2817",
          "brown-dark": "#2D1810",
          "brown-darker": "var(--brand-text)",
          "brown-light": "var(--brand-text-muted)",
          "brown-50": "var(--brand-tint-50)",
          "brown-100": "var(--brand-tint-100)",
          gold: "#F4B71F",
          "gold-bright": "#FFC72C",
          "gold-light": "#FFD66B",
          "gold-lighter": "#FCD34D",
          "gold-dark": "var(--brand-gold-dark)",
          "gold-pale": "#FEF3C7",
        },
        surface: {
          warm: "var(--brand-surface-warm)",
          cream: "var(--brand-surface)",
          "cream-50": "var(--brand-surface)",
          "off-white": "var(--brand-surface-warm)",
        },
        role: {
          superadmin: "#6B46C1",
          admin: "#B91C1C",
          director: "#F4B71F",
          hr: "#0F766E",
          manager: "#1E40AF",
          employee: "#3D2817",
          field: "#C2410C",
          trainer: "#15803D",
          intern: "#FCD34D",
        },
        // shadcn semantic tokens (mapped to brand)
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        success: { DEFAULT: "#5E8B3A", light: "#DCEEC9" },
        warning: { DEFAULT: "#E89F1A", light: "#FEF3C7" },
        error: { DEFAULT: "#C53030", light: "#FED7D7" },
        info: { DEFAULT: "#2C7A7B", light: "#C9E8E9" },
      },
      fontFamily: {
        display: ['"Playfair Display"', "serif"],
        body: ["Poppins", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": { transform: "scale(1)", opacity: "0.6" },
          "50%": { transform: "scale(1.1)", opacity: "1" },
        },
      },
      animation: {
        "pulse-glow": "pulse-glow 3s ease-in-out infinite",
      },
    },
  },
  plugins: [animate],
};

export default config;
