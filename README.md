# Terramedic

Terramedic Corps connects humans and AI to the environmental
organizations that need them. We offer people four pathways
to action — volunteer, donate, adopt everyday actions, or
make it a career — and we're building infrastructure for
AI agents to contribute too.

See [docs/STRATEGY.md](docs/STRATEGY.md) for our full
strategic direction.

## Public Domain Dedication for the term "terramedic"

Leila Hadj-Chikh came up with the word **"TerraMedics"**
as the name for her team at
[Conservation X Labs'](https://www.conservationxlabs.com/)
[Make for the Planet](https://www.makefortheplanet.com/)
competition at the inaugural Earth Optimism Summit in 2017
in Washington, DC.

The term "terramedic" is now intentionally placed in the
public domain by the originator of this term. It is free
for anyone to use, share, adapt, and apply in any context
— without restriction or attribution.

This dedication is made under
[Creative Commons Zero (CC0 1.0 Universal)](https://creativecommons.org/publicdomain/zero/1.0/),
which waives all rights to the term and affirms that it is
not, and should not be, treated as a trademark or
proprietary label.

We encourage everyone to use "terramedics" to describe
individuals and communities caring for the Earth.

## Tech Stack

**Frontend:**

- [SvelteKit](https://svelte.dev/) (Svelte 5) with
  TypeScript
- [Tailwind CSS](https://tailwindcss.com/) v4
- [Flowbite Svelte](https://flowbite-svelte.com/)
  component library
- [Storybook](https://storybook.js.org/) for component
  development
- Hosted on [Netlify](https://www.netlify.com/)

**Backend:**

- [Django](https://www.djangoproject.com/) with
  [Django Ninja](https://django-ninja.dev/) REST API
- PostgreSQL (PostGIS) in production, SpatiaLite locally
- Deployed to AWS Lambda via
  [Zappa](https://github.com/zappa/Zappa)

**Testing:**

- [Vitest](https://vitest.dev/) (unit/component tests)
- [Playwright](https://playwright.dev/) (end-to-end tests)
- [pytest](https://docs.pytest.org/) (backend tests)

**Code quality:**

- ESLint, Prettier (frontend)
- Ruff, mypy (backend)

## Getting Started

### Prerequisites

- Node.js 20+ and Yarn
- Python 3.14+ and [Poetry](https://python-poetry.org/)
- Git

### Frontend

```bash
git clone https://github.com/TerramedicCorps/terramedic.git
cd terramedic/terramedic
yarn install
yarn dev
```

### Backend

```bash
cd terramedic/backend
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

### Common Scripts

**Frontend** (run from `terramedic/`):

| Command | Description |
|---|---|
| `yarn dev` | Start development server |
| `yarn build` | Build for production |
| `yarn preview` | Preview production build |
| `yarn test:unit` | Run unit tests (Vitest) |
| `yarn test:e2e` | Run end-to-end tests (Playwright) |
| `yarn test` | Run all tests |
| `yarn lint` | Check linting |
| `yarn format` | Format code |
| `yarn storybook` | Launch Storybook |

**Backend** (run from `backend/`):

| Command | Description |
|---|---|
| `poetry run python manage.py runserver` | Start dev server |
| `poetry run pytest` | Run tests |
| `poetry run ruff check .` | Lint Python code |
| `poetry run mypy terramedic` | Type-check Python code |

## Project Structure

```text
terramedic/
├── terramedic/          # SvelteKit frontend
│   ├── src/
│   │   ├── routes/      # Pages (about, volunteer, donate, etc.)
│   │   └── lib/
│   │       ├── components/  # Reusable Svelte components
│   │       ├── server/      # Server-only utilities
│   │       └── utils/       # Client utilities
│   ├── e2e/             # Playwright end-to-end tests
│   ├── tests/           # Vitest unit tests
│   └── .storybook/      # Storybook configuration
├── backend/             # Django REST API
│   └── terramedic/
│       ├── core/        # Settings, URL routing, API config
│       └── organizations/  # Org models, API, admin
├── terraform/           # Infrastructure as code
├── docs/                # Strategy, architecture docs
└── .github/             # CI/CD workflows, PR templates
```

## Contributing

We welcome contributions! Whether you're fixing bugs,
adding features, improving documentation, or helping with
testing, your contributions are valued.

1. Read our [Contributing Guide](CONTRIBUTING.md)
2. Check out our [Code of Conduct](CODE_OF_CONDUCT.md)
3. Browse [open issues](https://github.com/TerramedicCorps/terramedic/issues)
   or create a new one
4. Fork the repository and create a feature branch
5. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for AI-assisted development
guidelines.

## Security

If you discover a security vulnerability, please review our
[Security Policy](SECURITY.md) for responsible disclosure
guidelines. Send reports to
[security@terramedic.org](mailto:security@terramedic.org).

## License

Code is licensed under
[GPL-3.0](gpl-3.0.txt). Non-code content is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
See [LICENSE.md](LICENSE.md) for details.

## Acknowledgements

- Ed Hawkins for creating the warming stripes visualization
- Climate science organizations for their data and research
- All the people working to build a sustainable future
