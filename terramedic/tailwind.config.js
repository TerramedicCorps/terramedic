/** @type {import('tailwindcss').Config} */
import aspectRatioPlugin from '@tailwindcss/aspect-ratio';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  /* Colors and fonts are defined via @theme in app.css (Tailwind v4).
     This config is only used for plugins; do not duplicate tokens here. */
  theme: {},
  plugins: [aspectRatioPlugin]
};
