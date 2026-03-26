import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "rgb(var(--color-primary) / <alpha-value>)",
          light: "rgb(var(--color-primary-light) / <alpha-value>)",
        },
        accent: { DEFAULT: "#D4A017", light: "#E6B422" },
        surface: {
          DEFAULT: "rgb(var(--color-surface) / <alpha-value>)",
          raised: "rgb(var(--color-surface-raised) / <alpha-value>)",
          alt: "rgb(var(--color-surface-alt) / <alpha-value>)",
        },
        danger: {
          DEFAULT: "rgb(var(--color-danger) / <alpha-value>)",
          bg: "rgb(var(--color-danger-bg) / <alpha-value>)",
        },
        success: {
          DEFAULT: "rgb(var(--color-success) / <alpha-value>)",
          bg: "rgb(var(--color-success-bg) / <alpha-value>)",
        },
        warning: {
          DEFAULT: "rgb(var(--color-warning) / <alpha-value>)",
          bg: "rgb(var(--color-warning-bg) / <alpha-value>)",
        },
        info: {
          DEFAULT: "rgb(var(--color-info) / <alpha-value>)",
          bg: "rgb(var(--color-info-bg) / <alpha-value>)",
        },
        neutral: {
          text: "rgb(var(--color-neutral-text) / <alpha-value>)",
          secondary: "rgb(var(--color-neutral-secondary) / <alpha-value>)",
          muted: "rgb(var(--color-neutral-muted) / <alpha-value>)",
          faint: "rgb(var(--color-neutral-faint) / <alpha-value>)",
          border: "rgb(var(--color-neutral-border) / <alpha-value>)",
          "border-light": "rgb(var(--color-neutral-border-light) / <alpha-value>)",
        },
      },
      fontFamily: {
        display: ['"Plus Jakarta Sans"', "sans-serif"],
        body: ['"DM Sans"', "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
      },
    },
  },
  plugins: [],
};
export default config;
