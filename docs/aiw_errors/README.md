# AIW Error Reporting

## Purpose

This folder stores structured AI Worker error reports generated when Copilot/AIW encounters execution, CI/CD, deployment, merge, Docker, Terraform, AWS, or runtime failures.

When CI/CD pipeline failures, Docker build failures, test failures, merge conflicts, deployment issues, or runtime errors occur, AIW (AI Worker) generates standardized error reports to enable rapid diagnosis and resolution.

## Error Report Location

All error reports are stored in this directory with the naming pattern:

```
YYYY-MM-DD_short-error-name.md
```

### Example Filename
```
2026-05-24_docker-build-failure.md
2026-05-24_test-import-error.md
2026-05-24_docker-hub-login-failure.md
```

## Error Report Format

Each error report **MUST** include the following sections:

### Error Summary
- Brief 1-2 line description of the failure
- Impact level (critical/high/medium/low)

### Execution Context
- **Branch**: The Git branch where the failure occurred
- **Command**: The exact command that was executed
- **Workflow**: The CI/CD workflow or task that failed
- **Environment**: The execution environment (GitHub Actions, local terminal, Docker, etc.)

### Exact Error
- Full error message and stack trace
- Error code or exit status if applicable
- Any system messages or warnings

### Failed Step
- Precise identification of which pipeline step failed
- Step name and number in the workflow

### Root Cause Hypothesis
- Initial analysis of why the failure occurred
- What changed that may have caused it

### Affected Files
- List of files involved in the failure
- File paths that were being processed when failure occurred

### Dependency / Sequencing Issues
- Any dependencies that may not have been met
- Sequencing problems in the pipeline
- Missing prerequisites

### What Was Already Tried
- Troubleshooting steps that have been attempted
- What worked and what didn't
- Previous attempts to fix the issue

### Recommended Next Action
- Clear next steps to diagnose or resolve
- Tools or commands to run
- Who/what should investigate further

### Operational Classification
- **Type**: execution | ci_cd | docker | deployment | merge | runtime | aws | terraform | dependency
- **Severity**: critical | high | medium | low
- **Recoverability**: manual | automatic | requires_code_change

### Safety Notes
- Any credentials that were visible (must be noted and rotated if exposed)
- Any data loss or corruption concerns
- Risk assessment for continuing or rolling back

## Error Report Lifecycle

1. **Creation**: Error is encountered → AIW creates report in this folder
2. **Commit**: Report is staged and committed with descriptive message
3. **Analysis**: Engineer reviews report and implements fix
4. **Resolution**: Root cause is fixed in code or configuration
5. **Archive**: Resolved reports remain for historical reference

## CI/CD Pipeline Failure Protocol

When ANY failure occurs in the pipeline:

1. **STOP guessing** — Gather exact error information
2. **CREATE error report** — Use format above
3. **DOCUMENT execution context** — Record branch, command, environment
4. **ANALYZE root cause** — Identify why it failed
5. **COMMIT report** — Stage and commit the error report
6. **RETURN path** — Provide error report path to user
7. **NO HIDING** — Do not suppress or hide failures
8. **NO OPTIONAL VALIDATION** — Do not skip validation steps to force success

## Docker Hub Publishing Pipeline

Current CI/CD flow for SPE-01:

```
feature branch / pull request
  → ci.yml (syntax, tests, Docker build validation — no push)
  → merge to main
  → docker-publish.yml
  → tests
  → Docker build
  → Docker Hub login
  → Docker Hub push (latest + commit SHA tags)
```

**Docker Hub Target**: `taig2k/finance_app_for_aws`

**Required Tags**:
- `latest` (points to most recent build from `main`)
- `<commit-sha>` (specific commit identifier)

Legacy note: Earlier pipeline used `deployable` branch and `taig2k/financial-nebula-node`. Retired in CI/CD-02.

## Related Documentation

- [CI Workflow](../.github/workflows/ci.yml)
- [Docker Publish Workflow](../.github/workflows/docker-publish.yml)
- [Dockerfile](../../Dockerfile)
- [Docker Configuration](../../config.docker.example.json)
- [Docker Usage Guide](../DOCKER_USAGE.md)

## Quick Start

If you encounter an error:

1. Create a new file: `YYYY-MM-DD_error-name.md`
2. Copy the template sections from above
3. Fill in each section with exact information
4. Commit with message: `Add AIW error report: <brief-description>`
5. Share the file path with the project team

---

**Last Updated**: 2026-05-24
**Governance Version**: 1.0
**Maintained By**: AI Worker (Copilot)
