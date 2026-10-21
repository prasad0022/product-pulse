# Product Pulse — Git & Branching Strategy

## Branches

- `main` — stable/demo-ready code only.
- `develop` — integration branch for completed features.
- `feature/<short-name>` — new features.
- `fix/<short-name>` — bug fixes.
- `docs/<short-name>` — documentation-only changes.

## Flow

Issue → feature branch → implementation → tests → Pull Request → review → `develop` → release PR → `main`.

## Commit convention

Use:
- `feat:` new functionality
- `fix:` bug fix
- `refactor:` code restructuring
- `test:` tests
- `docs:` documentation
- `chore:` tooling/configuration
