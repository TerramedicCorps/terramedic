import prettier from 'eslint-config-prettier';
import js from '@eslint/js';
import { includeIgnoreFile } from '@eslint/compat';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import { fileURLToPath } from 'node:url';
import ts from 'typescript-eslint';
import svelteConfig from './svelte.config.js';

const gitignorePath = fileURLToPath(new URL('../.gitignore', import.meta.url));

export default ts.config(
  includeIgnoreFile(gitignorePath),
  // .gitignore paths are relative to repo root, not this config's directory,
  // so build artifacts need explicit ignores here as well
  { ignores: ['build/', '.netlify/', '.svelte-kit/', 'test-results/'] },
  js.configs.recommended,
  ...ts.configs.recommended,
  ...svelte.configs.recommended,
  prettier,
  ...svelte.configs.prettier,
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node }
    },
    rules: {
      'no-undef': 'off',
      'svelte/no-navigation-without-resolve': 'off'
    }
  },
  {
    files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
    ignores: ['eslint.config.js', 'svelte.config.js'],
    languageOptions: {
      parserOptions: {
        projectService: true,
        extraFileExtensions: ['.svelte'],
        parser: ts.parser,
        svelteConfig
      }
    }
  },
  {
    files: ['**/*.svelte'],
    rules: {
      // Svelte 5 components are not event forwarders: an on: directive
      // on a component instance silently never fires (flowbite-svelte
      // 1.x receives handlers as callback props spread onto the
      // element). This bit us twice — OrganizationCard and ActionButton
      // analytics were dead after the Svelte 5 migration. Raw DOM
      // elements are unaffected and stay allowed.
      'no-restricted-syntax': [
        'error',
        {
          selector:
            'SvelteElement[kind="component"] > SvelteStartTag > SvelteDirective[kind="EventHandler"]',
          message:
            'on: event directives on components never fire in Svelte 5. Pass a callback prop instead (e.g. onclick={handler}, onclose={handler}).'
        },
        {
          // <svelte:component>/<svelte:self> parse as kind="special",
          // not "component", but still render component instances with
          // the same silent-no-op behavior. <svelte:element> and
          // <svelte:window> render real DOM targets and stay allowed.
          selector:
            'SvelteElement[kind="special"][name.name=/^svelte:(component|self)$/] > SvelteStartTag > SvelteDirective[kind="EventHandler"]',
          message:
            'on: event directives on <svelte:component>/<svelte:self> never fire in Svelte 5. Pass a callback prop instead (e.g. onclick={handler}).'
        }
      ]
    }
  }
);
