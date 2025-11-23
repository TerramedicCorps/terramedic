# Terramedic

Terramedic is a SvelteKit-powered platform providing resources, volunteer opportunities, and actionable solutions
for climate advocacy and sustainable living.

## Climate Action Hub

This website is designed to accompany warming stripes buttons distributed at climate outreach events.
The site explains what warming stripes represent and guides visitors toward meaningful climate action through
volunteering or donations.

## Public Domain Dedication for the term “terramedic”

Leila Hadj-Chikh came up with the word **"TerraMedics"** as the name for her team at
[Conservation X Labs'](https://www.conservationxlabs.com/) [Make for the Planet](https://www.makefortheplanet.com/)
competition at the inaugural Earth Optimism Summit in 2017 in Washington, DC.

The term "terramedic" is now intentionally placed in the public domain by the originator of this term.
It is free for anyone to use, share, adapt, and apply in any context — without restriction or attribution.

This dedication is made under [Creative Commons Zero (CC0 1.0 Universal)](https://creativecommons.org/publicdomain/zero/1.0/),
which waives all rights to the term and affirms that it is not, and should not be, treated as a trademark or
proprietary label.

We encourage everyone to use “terramedics” to describe individuals and communities caring for the Earth.

## Project Overview

This website aims to:

1. Educate people about warming stripes and climate change
2. Connect individuals with volunteer opportunities at climate organizations
3. Facilitate donations to effective climate action groups
4. Showcase ways for taking climate action in our daily lives
5. Provide outreach materiels and other resources for climate advocates

## Tech Stack

- **Frontend Framework**: Svelte
- **Styling**: Tailwind CSS
- **Component Development**: Storybook
- **Testing**: Playwright
- **Hosting**: Netlify

## Getting Started

### Prerequisites

- Node.js and Yarn installed
- Git installed

### Installation

```bash
# Clone the repository
git clone https://github.com/lhadjchikh/terramedic.git
cd terramedic

# Install dependencies
yarn install

# Start the development server
yarn dev
```

### Development Scripts

- `yarn dev` - Start development server
- `yarn build` - Build for production
- `yarn preview` - Preview production build locally
- `yarn storybook` - Launch Storybook for component development
- `yarn test` - Run Playwright tests

## Project Structure

- `/src/routes` - Svelte pages
- `/src/lib/components` - Reusable Svelte components
- `/src/lib/data` - Data files for organizations
- `/static` - Static assets
- `/tests` - Playwright tests
- `/.storybook` - Storybook configuration

## Adding Organizations

To add or update organizations, edit the data files in:

- `src/lib/data/volunteer-orgs.js` - For volunteer opportunities
- `src/lib/data/donation-orgs.js` - For donation options
- `src/lib/data/resource-orgs.js` - For resources available to climate advocates

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation,
or helping with testing, your contributions are valued.

### How to Contribute

1. Read our [Contributing Guide](CONTRIBUTING.md) for detailed guidelines
2. Check out our [Code of Conduct](CODE_OF_CONDUCT.md)
3. Browse [open issues](https://github.com/terramediccorps/terramedic/issues) or create a new one
4. Fork the repository and create a feature branch
5. Make your changes following our coding guidelines
6. Submit a pull request

### Development Workflow

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/terramedic.git
cd terramedic/terramedic

# Install dependencies
yarn install

# Start development server
yarn dev

# Run tests
yarn test

# Check linting
yarn lint

# Format code
yarn format
```

### Need Help?

- 📖 Read the [Contributing Guide](CONTRIBUTING.md)
- 🤖 Check [CLAUDE.md](CLAUDE.md) for AI-assisted development tips
- 💬 Join discussions in [GitHub Discussions](https://github.com/terramediccorps/terramedic/discussions)
- 🐛 Report bugs via [Issues](https://github.com/terramediccorps/terramedic/issues)

## Security

If you discover a security vulnerability, please review our [Security Policy](SECURITY.md) for responsible disclosure
guidelines. Send reports to [security@terramedic.org](mailto:security@terramedic.org).

## License

This project is licensed under the GNU General Public License v3.0 for code and the Creative Commons Attribution 4.0
International License (CC BY 4.0) for non-code content. See the [LICENSE](LICENSE.md) file for details.

## Acknowledgements

- Ed Hawkins for creating the warming stripes visualization
- Climate science organizations for their data and research
- All the climate activists working to build a sustainable future

This project was developed as a collaboration between humans and a group of AI tools, including:

- [GitHub Copilot](https://github.com/features/copilot)
- [Claude](https://claude.ai/) by Anthropic
- [ChatGPT](https://chat.openai.com/) by OpenAI
- [Gemini](https://gemini.google.com/) by Google
