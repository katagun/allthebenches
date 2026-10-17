# Security policy

Security fixes target the current main branch; historical snapshots are data artifacts, not separately maintained software releases.

For a vulnerability, use the repository's **Security → Report a vulnerability** private reporting feature when enabled. If unavailable, open an issue asking for a private contact without disclosing exploit details or secrets. Do not post credentials, sensitive URLs, or personal data in public reports.

Include affected versions, reproduction steps, impact, and a minimal example. No response-time guarantee is offered. Ordinary benchmark corrections belong in a public issue with source evidence.

The production site is static. Never embed API credentials in frontend code or `VITE_` variables. Collection credentials belong in local environment variables or GitHub Actions secrets. Required dependency audits check known advisories; they cannot guarantee the absence of unknown vulnerabilities.
