/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Cascadia Code'", "Consolas", "monospace"],
      },
      colors: {
        ink: {
          950: "#070b16",
          900: "#0b1020",
          850: "#0f1526",
          800: "#131a2e",
          700: "#1b2440",
          600: "#273252",
        },
        brand: {
          400: "#7aa2ff",
          500: "#5b8cff",
          600: "#3f6fe0",
        },
        // Redesign tokens (marketing + product shell)
        accent: {
          DEFAULT: "#8B5CF6",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8B5CF6",
          600: "#7c3aed",
          hover: "#A78BFA",
        },
        accent2: { DEFAULT: "#06B6D4", 400: "#22d3ee", 500: "#06B6D4" },
        success: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
        info: "#3B82F6",
        review: "#F97316",
        // UI_VISUAL_SPEC surface tokens (additive; legacy ink/brand kept)
        surface: "#111118",
        elevated: "#16161F",
        code: "#0D0D14",
      },
      borderRadius: {
        card: "1rem",
        "card-lg": "1.25rem",
        pill: "9999px",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(139,92,246,0.5), 0 0 28px rgba(139,92,246,0.25)",
        soft: "0 10px 40px rgba(0,0,0,0.45)",
        "glow-accent": "0 0 60px -15px rgba(139,92,246,0.5)",
        "glow-sm": "0 0 30px -10px rgba(139,92,246,0.35)",
        "glow-md": "0 0 60px -15px rgba(139,92,246,0.5)",
        "glow-cyan": "0 0 60px -15px rgba(6,182,212,0.4)",
        card: "0 1px 0 rgba(255,255,255,0.04), 0 8px 24px rgba(0,0,0,0.4)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(139,92,246,0.5)" },
          "70%": { boxShadow: "0 0 0 10px rgba(139,92,246,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(139,92,246,0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        floaty: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 1.8s infinite",
        floaty: "floaty 5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

