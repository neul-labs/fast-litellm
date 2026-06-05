# Security Policy

## Reporting a vulnerability

If you believe you've found a security vulnerability, please report it privately to **me@dipankar.name** rather than opening a public issue. Expect an initial acknowledgement within 48 hours.

When reporting, please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce, or a proof-of-concept where possible
- The affected version (or commit) of the project
- Any mitigations or workarounds you've identified

## Coordinated disclosure

We'll work with you to understand the issue, assess severity, and prepare a fix. We ask that you:

- Give a reasonable window for a fix to land before any public disclosure
- Avoid testing against shared infrastructure, third-party services, or other users' data
- Don't use the vulnerability beyond what's needed to demonstrate it

Once a fix is shipped, we're happy to credit the reporter in release notes unless they prefer to remain anonymous.

## Scope

This policy covers the source code in this repository. It does not cover:

- Third-party dependencies (please report those upstream first)
- Issues in user infrastructure caused by misconfiguration
- Vulnerabilities that require physical access to the system

## Supported versions

This project is under active development. Security fixes are typically applied to the `main` branch and the most recent tagged release. Older versions may not receive backports unless specifically requested.

## Out-of-scope research

We don't operate a bug bounty program. Reports are appreciated, and credit is given for valid findings, but we don't offer monetary rewards at this time.
