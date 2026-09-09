/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F6F7F5",
        card: "#FFFFFF",
        ink: "#14181C",
        muted: "#5B6169",
        hairline: "#E3E1D6",
        indigo: {
          DEFAULT: "#2F3B7A",
          hover: "#24305F",
          soft: "#EEF0FB",
        },
        teal: {
          DEFAULT: "#0F9D75",
          soft: "#E4F5EE",
        },
        amber: {
          DEFAULT: "#C97A2B",
          soft: "#FBEEDD",
        },
        brick: {
          DEFAULT: "#C1443B",
          soft: "#FBEAE8",
        },
      },
      fontFamily: {
        display: [
          "Nunito Sans",
          "Segoe UI",
          "-apple-system",
          "system-ui",
          "sans-serif",
        ],
        sans: [
          "-apple-system",
          "system-ui",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
      borderRadius: {
        card: "16px",
      },
      backgroundImage: {
        "dot-grid":
          "radial-gradient(circle, rgba(47,59,122,0.14) 1px, transparent 1px)",
      },
      backgroundSize: {
        "dot-grid": "18px 18px",
      },
    },
  },
  plugins: [],
};
