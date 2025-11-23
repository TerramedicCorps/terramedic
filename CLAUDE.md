# Claude.md - AI-Assisted Development Guide

This file provides context and guidelines for AI assistants (like Claude, ChatGPT, GitHub Copilot, etc.) working on the Terramedic project.

## Project Overview

Terramedic is a SvelteKit-powered climate action platform that provides:

- Educational content about climate change and warming stripes
- Connections to volunteer opportunities at climate organizations
- Donation options for effective climate action groups
- Resources for climate advocates and activists
- Daily actions for sustainable living

## Tech Stack

- **Framework**: SvelteKit (Svelte 5)
- **Styling**: Tailwind CSS v4
- **Component Library**: Flowbite Svelte
- **Testing**: Vitest (unit tests), Playwright (e2e tests)
- **Linting**: ESLint, Prettier
- **Type Checking**: TypeScript
- **Package Manager**: Yarn
- **Hosting**: Netlify

## Project Structure

```
terramedic/
├── src/
│   ├── routes/          # SvelteKit pages and routes
│   ├── lib/
│   │   ├── components/  # Reusable Svelte components
│   │   ├── data/        # Data files (transitioning to database)
│   │   └── ...
│   └── ...
├── static/              # Static assets
├── tests/               # Playwright e2e tests
├── e2e/                 # Additional e2e tests
└── .storybook/          # Storybook configuration
```

## Key Development Guidelines

### Code Style

- **Always run `yarn format` before committing** - Prettier is enforced
- **Run `yarn lint`** to check for ESLint issues
- Use TypeScript where beneficial, avoid `any` types
- Follow existing patterns in the codebase

### Svelte 5 Specific

- Use Svelte 5 runes (`$state`, `$derived`, `$effect`, etc.)
- Prefer composition over inheritance
- Keep components focused and single-responsibility
- Use `export let` for component props

### Styling

- Use Tailwind CSS utility classes
- Mobile-first responsive design
- Follow existing color scheme and design patterns
- Ensure accessibility (semantic HTML, ARIA labels, keyboard navigation)

### Testing

- Unit tests: Vitest with `@testing-library/svelte`
- E2E tests: Playwright
- Test files:
  - Unit: `*.test.ts` or `*.spec.ts` (server/general)
  - Component: `*.svelte.test.ts` (Svelte components)
  - E2E: `e2e/*.test.ts`
- **Important**: Run `yarn test` before submitting PRs

### Known Issues & Gotchas

1. **Test Configuration**: The project uses Vitest workspace mode with separate configurations for client (jsdom) and server (node) environments. SvelteKit modules are marked as external dependencies to avoid mocking issues.

2. **Database Migration**: The project is transitioning from hardcoded organization data to a database. Don't add new hardcoded organization data.

3. **Tailwind v4**: The project uses Tailwind CSS v4, which has some syntax differences from v3.

## Common Tasks

### Running the Project

```bash
yarn dev              # Start development server
yarn build            # Build for production
yarn preview          # Preview production build
yarn test             # Run all tests
yarn test:unit        # Run unit tests only
yarn test:e2e         # Run e2e tests only
yarn lint             # Check linting
yarn format           # Format code
yarn storybook        # Launch Storybook
```

### Adding a New Component

1. Create in `src/lib/components/`
2. Use TypeScript for props when beneficial
3. Add Storybook story if it's a reusable component
4. Write unit tests for complex logic
5. Ensure accessibility

### Adding a New Route

1. Create in `src/routes/[route-name]/`
2. Use `+page.svelte` for the page component
3. Use `+page.ts` or `+page.server.ts` for data loading
4. Add e2e test for critical user flows

## AI Assistant Guidelines

### When Writing Code

- **Review the existing codebase** before implementing new patterns
- **Follow the project's conventions** even if you know alternative approaches
- **Test thoroughly** - run `yarn test` and `yarn lint`
- **Keep commits focused** - one logical change per commit
- **Use conventional commits** format (see CONTRIBUTING.md)

### What to Avoid

- Don't introduce new dependencies without discussion
- Don't refactor working code unless specifically requested
- Don't add hardcoded organization data (use database)
- Don't skip writing tests for new features
- Don't ignore ESLint/Prettier errors

### When Unsure

- Check existing similar code in the project
- Refer to CONTRIBUTING.md for contribution guidelines
- Ask for clarification rather than making assumptions
- Suggest multiple approaches when appropriate

## Useful Context

### Warming Stripes

The project's core educational content centers around "warming stripes" - visualizations showing temperature change over time created by climate scientist Ed Hawkins.

### License

- **Code**: GPL-3.0
- **Non-code content**: CC BY 4.0

### Mission

The project aims to make climate action accessible and actionable for everyone. When contributing, consider:

- Accessibility for all users
- Clear, approachable language
- Mobile-first design
- Performance and efficiency
- Data accuracy and trustworthiness

## Questions or Issues?

- Check [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines
- Review existing issues and PRs for context
- When in doubt, ask for clarification
