# Contributing

Thanks for your interest in contributing. This project is part of an active development portfolio; APIs and behavior may change between releases. Issues and PRs are welcome.

## Reporting issues

When opening an issue, please include:

- The version (or commit) you're on
- Your platform / language runtime version
- A minimal reproduction
- What you expected vs. what happened

If you have a fix or workaround, mention it — even partial information helps.

## Pull requests

1. **Fork** the repository and create a feature branch from `main`.
2. **Make focused changes**: keep each PR scoped to one logical change.
3. **Add tests** for new behavior or bug fixes when there's a reasonable place to put them.
4. **Run existing tests** locally and ensure they pass.
5. **Write a clear commit message** that explains *why* the change is needed, not just *what* changed.
6. **Open a PR** with a description that covers motivation, approach, and any tradeoffs.

Smaller, well-described PRs are merged faster than large multi-purpose ones.

## Code style

- Match the existing style in the file you're editing.
- If the repo has a formatter or linter configured (`rustfmt`, `black`, `prettier`, etc.), run it before pushing.
- Add type annotations where the language supports them.
- Avoid drive-by reformatting unrelated code in the same PR.

## Tests

- Add tests for new behavior when there's a reasonable place to put them.
- Update tests that the change breaks rather than deleting them; if behavior is genuinely deprecated, document why in the PR.

## Documentation

- Update the README or docs site (`documentation/`) when public behavior changes.
- New features that are reachable from the public API need at least a one-paragraph note.

## Areas that need help

- Documentation polish and missing examples
- Test coverage on edge cases
- Platform-specific bug reports
- Real-world usage notes

## Code of conduct

- Be respectful and constructive.
- Focus on technical merit.
- Help others learn and improve.
- Don't tolerate harassment.

## Questions

Open an issue tagged `question` if you're unsure about:

- Whether a contribution is in scope
- How to set up the development environment
- Architecture or design decisions
- Whether a feature is planned

Reaching the maintainer privately: **me@dipankar.name**.
