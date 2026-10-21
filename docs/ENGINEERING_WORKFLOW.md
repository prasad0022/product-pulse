# Product Pulse Engineering Workflow

1. Create or update a GitHub Issue.
2. Create a feature branch.
3. Implement the smallest useful change.
4. Add/update tests.
5. Run the test suite.
6. Open a pull request.
7. Review the diff, docs, and risk.
8. Merge to the protected main branch.
9. CI runs automatically on push/PR.

## Quality gates
- No secrets in source control.
- Tests required for logic/API changes.
- Data contracts validated.
- Production code lives under `src/` or `api/`.
- Notebooks are for exploration and analysis, not service implementation.
