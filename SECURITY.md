# Security Policy

## Supported scope

Security reports should target the current `main` branch and the deployed IPO Tracker surfaces, including GitHub Actions workflows, GitHub Pages assets, repository automation, and data-pipeline code.

Historical branches, archived evidence, and superseded one-shot workflows are retained for auditability but are not supported production surfaces.

## Reporting a vulnerability

Please do not publish credentials, exploit details, private tokens, or sensitive reproduction data in a public issue.

Use GitHub's **private vulnerability reporting / Security Advisory** flow for this repository when it is available. If private reporting is unavailable, open a minimal public issue stating that you need a private security contact channel, without including exploit details.

For ordinary non-sensitive bugs, use the normal issue tracker.

## Security expectations

Contributions must not:

- commit secrets, tokens, credentials, or private keys;
- weaken official-source host validation or evidence integrity checks;
- silently expand GitHub Actions write permissions;
- add unreviewed direct-to-`main` publication paths;
- bypass source, hash, schema, identity, or publication-verification safeguards.

Security fixes should include regression coverage appropriate to the affected surface.
