/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#080B14',
        surface: '#10162A',
        surface2: '#161D38',
        edge: '#242C4B',
        violet: {
          DEFAULT: '#7C5CFF',
          dim: '#5B3FE0',
          glow: '#9D86FF',
        },
        cyan: {
          DEFAULT: '#2DD4FF',
          dim: '#0EA5C7',
        },
        safe: {
          DEFAULT: '#2EE6A6',
          dim: '#15A87A',
        },
        danger: {
          DEFAULT: '#FF4D6D',
          dim: '#D6294A',
        },
        muted: '#8B96B5',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        body: ['Inter', 'sans-serif'],
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        radar: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        pulseRing: {
          '0%': { transform: 'scale(0.9)', opacity: '0.8' },
          '100%': { transform: 'scale(1.8)', opacity: '0' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
        rise: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        scan: 'scan 4s linear infinite',
        radar: 'radar 6s linear infinite',
        pulseRing: 'pulseRing 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        blink: 'blink 1.6s ease-in-out infinite',
        rise: 'rise 0.6s ease-out both',
      },
      backgroundImage: {
        grid: 'linear-gradient(rgba(124,92,255,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(124,92,255,0.08) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
}
