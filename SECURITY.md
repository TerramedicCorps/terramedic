# Security Policy

## Reporting a Vulnerability

The Terramedic team takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by:

1. **Email**: Send details to [security@terramedic.org](mailto:security@terramedic.org)
2. **GitHub Security Advisories**: Use the
   [Security Advisories](https://github.com/terramediccorps/terramedic/security/advisories) feature

### What to Include

When reporting a vulnerability, please include:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 48 hours, we'll acknowledge receipt of your report
- **Status Update**: Within 7 days, we'll provide a more detailed response indicating next steps
- **Fix Timeline**: We'll work to fix confirmed vulnerabilities as quickly as possible

### What to Expect

After submitting a vulnerability report:

1. We'll confirm the vulnerability and determine its impact
2. We'll develop and test a fix
3. We'll release a patch and publicly disclose the vulnerability (crediting you if desired)
4. We'll update this document with the resolution

## Supported Versions

Currently, only the latest version deployed to production is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| Older   | :x:                |

## Security Best Practices

This project follows security best practices including:

- Regular dependency updates via Dependabot
- CodeQL security scanning on all pull requests
- Automated security audits in CI/CD pipeline
- Adherence to OWASP guidelines

## Bug Bounty

Currently, we do not offer a paid bug bounty program. However, we deeply appreciate security researchers
who help make Terramedic safer for everyone.

## Disclosure Policy

- Please give us reasonable time to fix the issue before public disclosure
- We'll credit you in our security advisories (unless you prefer to remain anonymous)
- We're committed to working with researchers in good faith

Thank you for helping keep Terramedic and its users safe!
