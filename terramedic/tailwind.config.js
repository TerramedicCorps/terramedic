/** @type {import('tailwindcss').Config} */
import aspectRatioPlugin from '@tailwindcss/aspect-ratio';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        'space-black': '#0a0e17',
        'deep-navy': '#0f1829',
        navy: '#162033',
        'terra-green': '#2ecc71',
        'terra-blue': '#2196f3',
        'terra-dark-blue': '#0f1829',
        'sunrise-gold': '#f39c12',
        'text-secondary': '#b0bec5'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['Merriweather', 'serif'],
        mono: ['Courier New', 'monospace']
      }
    }
  },
  plugins: [aspectRatioPlugin]
};
