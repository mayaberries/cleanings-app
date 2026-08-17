// Single source of truth for the Tailwind CDN color/font tokens used by
// every Astro project in this repo (frontend/template, frontend/admin).
//
// TODO: Prototype-only setup, same caveat as before: this is a plain object fed
// into the Tailwind CDN's `tailwind.config`, not a real tailwind.config.*.
// Swap for a real Tailwind build pipeline (and this file for a proper
// config module) before any of this ships.

export const colors = {
    base: "#F1F3EE",
    ink: "#172E29",
    inksoft: "#4B5D58",
    surface: "#FFFFFF",
    line: "#DCE1D9",
    gold: "#E3A039",
    goldsoft: "#F7DBA6",
    teal: "#3F7377",
    panel: "#F7F9F4",
    muted: "#4B5D58",
    danger: "#B3492F",
    dangersoft: "#F5DED7",
    primary: { DEFAULT: "#3F7377", dark: "#2F5A5D" },
    accent: { DEFAULT: "#E3A039", dark: "#C1841F", light: "#F7DBA6" },
};

export const fontFamily = {
    display: ['"Space Grotesk"', "sans-serif"],
    body: ['"Inter"', "sans-serif"],
    sans: ['"Inter"', "sans-serif"],
    mono: ['"IBM Plex Mono"', "monospace"],
};

export const googleFontsHref =
    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap";
