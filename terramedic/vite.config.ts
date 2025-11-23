import { svelteTesting } from '@testing-library/svelte/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// More info at: https://storybook.js.org/docs/writing-tests/test-addon
export default defineConfig({
  resolve: {
    alias: {
      $lib: '/src/lib'
    }
  },
  plugins: [sveltekit()],
  css: {
    postcss: true // Ensure PostCSS is used
  },
  test: {
    server: {
      deps: {
        external: ['@sveltejs/kit']
      }
    },
    projects: [
      {
        extends: './vite.config.ts',
        plugins: [svelteTesting()],
        test: {
          name: 'client',
          environment: 'jsdom',
          clearMocks: true,
          include: ['src/**/*.svelte.{test,spec}.{js,ts}'],
          exclude: ['src/lib/server/**'],
          setupFiles: ['./vitest-setup-client.ts']
        }
      },
      {
        extends: './vite.config.ts',
        test: {
          name: 'server',
          environment: 'node',
          include: ['src/**/*.{test,spec}.{js,ts}'],
          exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
        }
      }
    ]
  }
});
