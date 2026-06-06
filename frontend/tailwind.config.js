/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bnpl: {
          navy: "#0a192f",
          "navy-soft": "#0d1c32",
          orange: "#ff8c00",
          amber: "#ffb77d",
          surface: "#fbf9fb",
          "surface-low": "#f5f3f5",
          "surface-card": "#ffffff",
          "surface-line": "#c5c6cd",
          ink: "#1b1b1d",
          muted: "#44474d",
          success: "#15803d",
          danger: "#ba1a1a",
        },
      },
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        bnpl: "0 4px 20px rgba(10, 25, 47, 0.04)",
        "bnpl-soft": "0 18px 60px rgba(10, 25, 47, 0.08)",
      },
      borderRadius: {
        card: "1rem",
      },
    },
  },
  plugins: [],
};
