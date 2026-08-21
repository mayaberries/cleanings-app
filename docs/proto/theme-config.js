// Shared Tailwind CDN config — same tokens as frontend/admin's design system
// (frontend/admin/shared/design-tokens.mjs). Every page in this prototype
// loads this file, in this order, in its <head>:
//   <script src="https://cdn.tailwindcss.com"></script>
//   <script src="theme-config.js"></script>
// Order matters: this has to run (as a plain, blocking <script src>, not
// defer/async) after the Tailwind CDN script defines `tailwind`, and before
// Tailwind's DOMContentLoaded class scan runs.
tailwind.config = {
  theme: {
    extend: {
      colors: {
        base: "#F1F3EE", ink: "#172E29", inksoft: "#4B5D58", surface: "#FFFFFF",
        line: "#DCE1D9", gold: "#E3A039", goldsoft: "#F7DBA6", teal: "#3F7377",
        panel: "#F7F9F4", muted: "#4B5D58",
        primary: { DEFAULT: "#3F7377", dark: "#2F5A5D" },
        accent: { DEFAULT: "#E3A039", dark: "#C1841F", light: "#F7DBA6" },
      },
      fontFamily: {
        display: ['"Space Grotesk"', "sans-serif"],
        body: ['"Inter"', "sans-serif"],
        sans: ['"Inter"', "sans-serif"],
        mono: ['"IBM Plex Mono"', "monospace"],
      },
    },
  },
};
