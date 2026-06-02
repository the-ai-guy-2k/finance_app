# Governance

## Branch Strategy

- **Feature branches**: Use descriptive names, e.g., `feature/csv-upload`, `fix/config-error`
- **Local testing**: Test all flows locally before push
- **GitHub Actions CI**: All commits trigger CI (syntax check, import test, pytest)
- **Deployable branch**: Merge feature branch to `deployable` only after CI passes
- **Deployable = Stable**: Only production-ready, tested code

## Commit Standards

- Clear, descriptive commit messages
- One logical change per commit
- Reference issue/task if applicable

Example:
```
feat: add preflight validation for config and API key
- validate config.json on startup
- check OpenAI API key file exists
- log errors with timestamps
```

## Operational Discipline

- Do NOT merge to deployable until CI passes
- Keep changes minimal and focused on MVP scope
- All git operations performed by Copilot workflow automation
- No manual hotfixes to deployable branch

## OpenAI SDK Compatibility Governance

- Do not pin legacy SDK versions unless explicitly approved
- Prefer modern SDK-compatible code over downgrading dependencies
- Fix code to support the current OpenAI SDK
- Log SDK compatibility issues and document fixes

## AI Response Format Governance

- AI responses used by application logic must be constrained, validated, and safely parsed before use
- Prefer strict JSON response instructions for structured outputs
- Handle markdown wrappers, empty responses, and malformed JSON with fallback behavior
- Log response length, preview, and validation outcome without exposing secrets

## Operational Logs Governance

- Every feature add must update `CHANGELOG.md`.
- Every runtime bug must update `docs/BUG_FIX_LOG.md`.
- Every AI/Copilot execution failure should be classified and logged.
- Logs should support future troubleshooting, passdowns, and operational continuity.

## UI Governance

- MVP UI must remain functional-first and professional.
- UI must not imply features that do not exist.
- Visual improvements should support operational clarity and readability.
- Keep styling lightweight and maintainable (CSS-only, no complex frameworks).
- Use feature branches for all UI changes and validate locally before merging.
- Avoid flashy animations, dark-mode-only designs, or overbuilt dashboard widgets.

## Docker Governance

- Feature branches and pull requests run CI validation only (no Docker Hub push).
- The `main` branch triggers `docker-publish.yml`, which builds and publishes `taig2k/finance_app_for_aws` to Docker Hub.
- Docker Hub credentials are stored only as GitHub Actions secrets (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`).
- Docker Hub publishing requires all tests to pass first.
- Docker Hub publishing is blocked if any test or build step fails.
- Docker images are tagged with `latest` and commit SHA.
- No secrets are baked into images; all configs are mounted at runtime.

Legacy note: Earlier governance referenced a `deployable` branch and `taig2k/financial-nebula-node`. SPE-01 uses `main` and `taig2k/finance_app_for_aws` instead.

## MVP Scope Lock

Containerization is allowed through explicit feature branches and CI-validated workflows.

Do NOT add:
- Database
- Authentication
- Advanced UI frameworks
- Microservices
- Cloud infrastructure

Focus on: local-first, operationally testable execution.

## Branch Closeout Governance

Feature branches follow this lifecycle:

ACTIVE
→ VALIDATED
→ MERGED or NOT_MERGED
→ CLOSED

Rules:
- Closed branches are historical artifacts only.
- No further development should continue on closed branches.
- New work requires a new feature branch.
- Branch closeout records must be created for completed feature branches in `docs/branch_closeouts/`.
- Remote branch deletion requires explicit user approval and is NOT performed automatically.

Include the branch closeout process in N.O.C. Art Guidance to prevent AIWs from continuing work on completed branches.

N.O.C. Guidance Note:
- Branch closeout guidance should be included in any future N.O.C. Art Guidance so AI Workers do not continue work on completed branches.

