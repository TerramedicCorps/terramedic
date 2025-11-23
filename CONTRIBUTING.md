# Contributing to Terramedic

Thank you for your interest in contributing to Terramedic! This project aims to provide resources and opportunities
for climate action, and we welcome contributions from everyone who shares this mission.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow.
Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/terramediccorps/terramedic/issues)
- If not, create a new issue using the bug report template
- Include as much detail as possible: steps to reproduce, expected vs actual behavior, screenshots, etc.

### Suggesting Enhancements

- Check if the enhancement has already been suggested
- Create a new issue using the feature request template
- Clearly describe the feature and its benefits

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our coding guidelines
4. Test your changes thoroughly
5. Commit using conventional commit messages
6. Push to your fork
7. Open a Pull Request

## Development Setup

### Prerequisites

- Node.js 20.x or higher
- Yarn package manager
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/terramedic.git
cd terramedic/terramedic

# Or clone the main repo
git clone https://github.com/terramediccorps/terramedic.git
cd terramedic/terramedic

# Install dependencies
yarn install

# Start development server
yarn dev
```

### Available Scripts

- `yarn dev` - Start development server
- `yarn build` - Build for production
- `yarn preview` - Preview production build
- `yarn test` - Run all tests (unit + e2e)
- `yarn test:unit` - Run unit tests
- `yarn test:e2e` - Run e2e tests
- `yarn lint` - Run ESLint and Prettier checks
- `yarn format` - Format code with Prettier
- `yarn storybook` - Launch Storybook for component development

## Coding Guidelines

### Code Style

- We use **Prettier** for code formatting (automatically enforced)
- We use **ESLint** for code quality
- Run `yarn format` before committing
- Run `yarn lint` to check for issues

### TypeScript

- Use TypeScript for type safety where beneficial
- Avoid using `any` type unless absolutely necessary
- Add JSDoc comments for complex functions

### Svelte Components

- Use Svelte 5 syntax and features
- Keep components focused and reusable
- Use props for component configuration
- Follow existing component patterns in `/src/lib/components`

### Styling

- Use Tailwind CSS utility classes
- Follow the existing design system
- Ensure responsive design (mobile-first)
- Test on different screen sizes

### Accessibility

- Use semantic HTML
- Include ARIA labels where needed
- Ensure keyboard navigation works
- Test with screen readers when possible

### Testing

- Write unit tests for new components using Vitest
- Write e2e tests for critical user flows using Playwright
- Ensure all tests pass before submitting PR
- Aim for meaningful test coverage

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```text
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependencies

### Examples

```text
feat(search): add filter functionality for organizations

Implemented client-side filtering for volunteer opportunities
with support for keyword search and category filters.

Closes #123
```

```text
fix(navigation): correct mobile menu behavior

The mobile navigation was not closing after selecting a link.
Fixed event handler to properly toggle menu state.
```

## Pull Request Process

1. **Update Documentation**: If you've added features, update the README or relevant docs
2. **Add Tests**: Include tests for new functionality
3. **Run All Checks**: Ensure `yarn lint` and `yarn test` pass
4. **Fill Out Template**: Complete the PR template with all relevant information
5. **Link Issues**: Reference any related issues
6. **Request Review**: Tag maintainers if needed
7. **Address Feedback**: Respond to review comments promptly
8. **Keep Updated**: Rebase or merge main if your branch falls behind

### PR Title Format

Use conventional commit format in PR titles:

- `feat: add volunteer search functionality`
- `fix: correct mobile navigation bug`
- `docs: update installation instructions`

## Issue Guidelines

### Before Creating an Issue

- Search existing issues to avoid duplicates
- Check if it's already fixed in the latest version
- Gather relevant information (browser, OS, steps to reproduce)

### Issue Templates

Use the appropriate template:

- **Bug Report**: For reporting bugs
- **Feature Request**: For suggesting new features

### Writing Good Issues

- **Clear Title**: Descriptive and specific
- **Detailed Description**: Explain the problem or suggestion thoroughly
- **Steps to Reproduce** (for bugs): List exact steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots**: Include if helpful
- **Environment**: Browser, OS, Node version, etc.

## AI-Assisted Development

This project welcomes contributions made with AI assistance. If you're using AI tools like GitHub Copilot, Claude, or ChatGPT:

- Review all AI-generated code carefully
- Ensure it follows our coding guidelines
- Test thoroughly
- Feel free to mention AI assistance in PR descriptions (optional)
- See [CLAUDE.md](CLAUDE.md) for project-specific AI development guidelines

## Questions?

If you have questions about contributing:

- Check existing documentation
- Look through closed issues for similar questions
- Open a new issue with the question label
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under:

- **Code**: GNU General Public License v3.0
- **Non-code content**: Creative Commons Attribution 4.0 International License (CC BY 4.0)

Thank you for contributing to climate action through Terramedic!
