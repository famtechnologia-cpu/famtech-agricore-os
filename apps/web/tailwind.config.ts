import type { Config } from 'tailwindcss'
const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#10b981', dark: '#059669', light: '#34d399', dim: 'rgba(16,185,129,0.12)' },
        surface: { DEFAULT: '#0f1117', raised: '#161921', border: 'rgba(255,255,255,0.06)' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Outfit', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config
