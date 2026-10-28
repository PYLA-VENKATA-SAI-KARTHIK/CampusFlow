/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Space Grotesk"', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Space Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        lilac: {
          50: '#f6f3fc',
          100: '#eee7fa',
          200: '#ddd0f5',
          300: '#c1aeee',
          400: '#a78be6',
          500: '#9b86d9', // Signature referral color
          600: '#8367ca',
          700: '#6d50b4',
          800: '#5a4195',
          900: '#4b3679',
          950: '#2a1c4b',
        },
        obsidian: {
          800: '#1c1e2a',
          850: '#15161f',
          900: '#0e0f15',
          950: '#07080b',
        },
        primary: {
          50: '#f6f3fc',
          100: '#eee7fa',
          200: '#ddd0f5',
          300: '#c1aeee',
          400: '#a78be6',
          500: '#9b86d9',
          600: '#8367ca',
          700: '#6d50b4',
          800: '#5a4195',
          900: '#4b3679',
        }
      }
    },
  },
  plugins: [],
}
