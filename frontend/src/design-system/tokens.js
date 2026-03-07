/**
 * Design tokens da Logia Marketing Platform.
 * Fonte única de verdade — importado pelo tailwind.config.js e componentes.
 */

// ── Cores ─────────────────────────────────────────────────────────────────────

export const colors = {
  // Marca
  primary:          "#6366F1",  // indigo — tecnologia + confiança
  "primary-dark":   "#4F46E5",
  "primary-light":  "#818CF8",
  secondary:        "#10B981",  // emerald — crescimento + sucesso
  "secondary-dark": "#059669",

  // Semânticas
  danger:   "#EF4444",
  warning:  "#F59E0B",
  info:     "#3B82F6",
  success:  "#22C55E",

  // Superfícies (dark mode)
  background:         "#0F0F0F",
  surface:            "#1A1A1A",
  "surface-elevated": "#242424",
  "surface-overlay":  "#2A2A2A",

  // Bordas
  border:        "#2E2E2E",
  "border-focus": "#6366F1",

  // Texto
  "text-primary":   "#F9FAFB",
  "text-secondary": "#9CA3AF",
  "text-muted":     "#6B7280",
  "text-disabled":  "#4B5563",

  // Canais sociais
  instagram: "#E1306C",
  linkedin:  "#0A66C2",
  twitter:   "#000000",
  youtube:   "#FF0000",
  email:     "#6366F1",
};

// ── Tipografia ────────────────────────────────────────────────────────────────

export const fontFamily = {
  sans: ['"Inter"', "system-ui", "sans-serif"],
  mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
};

export const fontSize = {
  xs:   ["11px", { lineHeight: "16px" }],
  sm:   ["13px", { lineHeight: "20px" }],
  base: ["14px", { lineHeight: "22px" }],
  lg:   ["16px", { lineHeight: "24px" }],
  xl:   ["18px", { lineHeight: "28px" }],
  "2xl":["24px", { lineHeight: "32px" }],
  "3xl":["30px", { lineHeight: "38px" }],
  "4xl":["36px", { lineHeight: "44px" }],
};

// ── Espaçamento (escala de 4px) ───────────────────────────────────────────────

export const spacing = {
  1:  "4px",
  2:  "8px",
  3:  "12px",
  4:  "16px",
  6:  "24px",
  8:  "32px",
  12: "48px",
  16: "64px",
};

// ── Border radius ─────────────────────────────────────────────────────────────

export const borderRadius = {
  sm:   "4px",
  md:   "8px",
  lg:   "12px",
  xl:   "16px",
  "2xl":"20px",
  full: "9999px",
};

// ── Sombras ───────────────────────────────────────────────────────────────────

export const boxShadow = {
  sm:          "0 1px 3px rgba(0,0,0,0.4)",
  md:          "0 4px 12px rgba(0,0,0,0.5)",
  lg:          "0 8px 32px rgba(0,0,0,0.6)",
  xl:          "0 16px 48px rgba(0,0,0,0.7)",
  "glow-primary":   "0 0 20px rgba(99,102,241,0.3)",
  "glow-secondary": "0 0 20px rgba(16,185,129,0.3)",
  "glow-danger":    "0 0 16px rgba(239,68,68,0.3)",
  "inner-sm":  "inset 0 1px 3px rgba(0,0,0,0.4)",
};

// ── Animações ─────────────────────────────────────────────────────────────────

export const keyframes = {
  "pulse-glow": {
    "0%, 100%": { opacity: "1", boxShadow: "0 0 8px rgba(99,102,241,0.3)" },
    "50%":       { opacity: "0.75", boxShadow: "0 0 20px rgba(99,102,241,0.6)" },
  },
  "pulse-glow-green": {
    "0%, 100%": { opacity: "1", boxShadow: "0 0 8px rgba(16,185,129,0.3)" },
    "50%":       { opacity: "0.75", boxShadow: "0 0 20px rgba(16,185,129,0.6)" },
  },
  "cursor-blink": {
    "0%, 100%": { opacity: "1" },
    "50%":      { opacity: "0" },
  },
  "score-fill": {
    "0%":   { width: "0%" },
    "100%": { width: "var(--score-width)" },
  },
  "fade-in": {
    "0%":   { opacity: "0", transform: "translateY(4px)" },
    "100%": { opacity: "1", transform: "translateY(0)" },
  },
  "shimmer": {
    "0%":   { backgroundPosition: "-200% 0" },
    "100%": { backgroundPosition: "200% 0" },
  },
};

export const animation = {
  "pulse-glow":       "pulse-glow 2s ease-in-out infinite",
  "pulse-glow-green": "pulse-glow-green 2s ease-in-out infinite",
  "cursor-blink":     "cursor-blink 1s step-end infinite",
  "score-fill":       "score-fill 0.8s ease-out forwards",
  "fade-in":          "fade-in 0.2s ease-out",
  "shimmer":          "shimmer 2s linear infinite",
};

// ── Export agregado (para tailwind.config.js) ─────────────────────────────────

export default {
  colors,
  fontFamily,
  fontSize,
  spacing,
  borderRadius,
  boxShadow,
  keyframes,
  animation,
};
