# Contributing & Git Workflow

Thank you for contributing to MCP-PowerBi-Finvision. This guide describes the branching model, commit conventions, testing, and release process so changes ship safely and predictably.

## Branching model

- main: always green; production-ready. Tag releases from here.
- feat/\<name\>: new features. Small, focused PRs preferred.
- fix/\<name\>: bug fixes.
- docs/\<name\>: documentation-only changes.
- chore/\<name\>: non-functional changes (tooling, CI, formatting).

## Commits

- Use clear, imperative messages: "Add rate limit stats endpoint".
- Reference issues when applicable: "Fix #123: ...".
- Keep PRs small; split refactors from behavior changes.

## Versioning

- Follow semantic-ish minor bumps as needed and keep `__version__.py` aligned.
- Update README.md and INSTALL.md dates when making notable end-user changes.

## Quality gates

Before opening a PR:

- Lint/Typecheck: PASS (Markdown formatting, Python static checks if configured)
- Unit tests: PASS (Run the task "Run unit tests")
- Manual smoke: Optional but encouraged (Power BI Desktop open with a sample PBIX)

## Local test commands (Windows PowerShell)

```powershell
# Run unit tests via VS Code task (recommended) or directly
# Task: "Run unit tests" (via Terminal > Run Task)

# Or direct invocation
venv\Scripts\python.exe -m unittest discover -v

# Quick smoke to validate tool wiring (requires Desktop running)
venv\Scripts\python.exe scripts\dev\run_all_tools_smoke.py
```

## Release process

1. Ensure main is green (tests PASS). Bump version in `__version__.py`.
2. Update CHANGELOG summary in README.md (Changelog section) if needed.
3. Tag the commit: `vX.Y.Z`.
4. Create a GitHub Release with highlights and link to INSTALL.md.
5. Optional: publish docs/ to Pages if configured.

## Code style & docs

- Python: match existing style; prefer small, pure functions and explicit error envelopes.
- Docs: keep README.md concise; move detail to INSTALL.md or docs/*.md
- Screenshots: store under docs/img/ and reference with relative paths.

## Security & privacy

- Avoid adding any network calls; server must operate locally.
- Validate all user inputs; never execute raw DAX/M without checks.
- Keep defaults conservative (rate limiting ON, validation ON).

---

Questions? Open an issue or start a discussion.
