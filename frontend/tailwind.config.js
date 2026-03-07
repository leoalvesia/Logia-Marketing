import tokens from "./src/design-system/tokens.js";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // ── Shadcn/ui CSS variable colours (kept for component compatibility) ──
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
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
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },

        // ── Design System tokens (logia.* namespace) ──────────────────────
        logia: tokens.colors,
      },

      // ── Typography ────────────────────────────────────────────────────────
      fontFamily: tokens.fontFamily,
      fontSize: tokens.fontSize,

      // ── Spacing ───────────────────────────────────────────────────────────
      spacing: tokens.spacing,

      // ── Border radius (merges with shadcn/ui --radius var) ────────────────
      borderRadius: {
        ...tokens.borderRadius,
        // shadcn/ui compat
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },

      // ── Shadows ───────────────────────────────────────────────────────────
      boxShadow: tokens.boxShadow,

      // ── Animations ────────────────────────────────────────────────────────
      keyframes: {
        ...tokens.keyframes,
        "slide-in-right": {
          from: { transform: "translateX(110%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        "slide-out-right": {
          from: { transform: "translateX(0)", opacity: "1" },
          to: { transform: "translateX(110%)", opacity: "0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        ...tokens.animation,
        "slide-in-right": "slide-in-right 0.25s cubic-bezier(0.16,1,0.3,1)",
        "slide-out-right": "slide-out-right 0.2s ease-in",
        "fade-in": "fade-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};
