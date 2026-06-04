# ACI-PA-04 — Security Remediation Merge + Artifact Publish

**Project:** Financial App  
**Date:** 2026-06-04  
**Scope:** Merge, CI/CD artifact publish verification only (no Terraform apply, PE, PAPE)  
**Release branch:** `deployable`

---

## Executive Summary

P0 security remediation (`feature/pape-p0-security-remediation`) was **fast-forward merged** into `deployable`. Initial publish at `def52aa` **failed CI/Docker Publish** (CSRF tests vs. preflight on Linux). Follow-up commit `5175aa9` fixed CI; **CI and Docker Publish succeeded**. Docker Hub now exposes pin tag `5175aa9f31ef9889b06df2043215b7c0837e08ba` and `latest` at the same digest.

**Artifact status:** **READY for ACI-PE-04** (pin new SHA; PE still on old image until redeploy).

---

## 1. Branch Status

| Item | Value |
|------|--------|
| Working branch | `deployable` |
| Security feature branch | `feature/pape-p0-security-remediation` (pushed; tip `def52aa`) |
| Security commit | `def52aa93dd8869dd29b872ad94a07ebd2747dd7` — `ACI-SECURITY-02: implement P0 security remediation bundle` |
| CI fix commit | `5175aa9f31ef9889b06df2043215b7c0837e08ba` — `ACI-PA-04: fix CI CSRF tests when preflight fails without local key file` |
| `origin/deployable` | Up to date with `5175aa9` |

---

## 2. Merge Result

| Step | Result |
|------|--------|
| Merge `feature/pape-p0-security-remediation` → `deployable` | **Fast-forward**, no conflicts |
| Pre-merge tip | `1c8bbe6` (ACI-PE-01 report) |
| Post-security-merge tip | `def52aa` |
| Post-CI-fix tip | `5175aa9` |

---

## 3. Test Result

| Environment | Command | Result |
|-------------|---------|--------|
| Local (Windows) | `pytest -v` | **28 passed** |
| GitHub Actions `def52aa` | `pytest tests/ -v` | **Failed** (CSRF tests: `/add_transaction` redirected when `PREFLIGHT_SUCCESS=False`) |
| GitHub Actions `5175aa9` | `pytest tests/ -v` | **Passed** (with `OPENAI_API_KEY` CI env + CSRF test preflight override) |

---

## 4. Terraform Validate Result

| Path | Command | Result |
|------|---------|--------|
| `terraform/spe-01/` | `terraform validate` | **Success** (local, post-merge) |

No `terraform apply` performed (scope).

---

## 5. GitHub Actions Result

### Failed (security merge only — `def52aa`)

| Workflow | Run ID | Conclusion | URL |
|----------|--------|------------|-----|
| CI | 26973779918 | **failure** | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26973779918 |
| Docker Publish | 26973779863 | **failure** | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26973779863 |

**Root cause:** Tracked `config.json` references a Windows-only OpenAI key path; on Ubuntu CI preflight fails, `/add_transaction` redirects before CSRF token extraction (`test_csrf_allows_post_with_token`).

### Succeeded (publishable tip — `5175aa9`)

| Workflow | Run ID | Conclusion | URL |
|----------|--------|------------|-----|
| CI | 26974235580 | **success** | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26974235580 |
| Docker Publish | 26974235574 | **success** | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26974235574 |

---

## 6. Docker Image Tags

**Repository:** `taig2k/finance_app_for_aws`  
**Hub:** https://hub.docker.com/r/taig2k/finance_app_for_aws/tags  

| Tag | Deployable SHA | Last pushed (UTC) | Manifest digest |
|-----|----------------|-------------------|-----------------|
| `5175aa9f31ef9889b06df2043215b7c0837e08ba` | `5175aa9` (publish tip) | 2026-06-04T19:23:20Z | `sha256:c2712791f301195bf99389c158e262368ad1935abd00544cf92f9d76c44c8c7` |
| `latest` | Same as `5175aa9…` | 2026-06-04T19:23:18Z | `sha256:c2712791f301195bf99389c158e262368ad1935abd00544cf92f9d76c44c8c7` |
| `def52aa93dd8869dd29b872ad94a07ebd2747dd7` | — | **Not published** (publish failed on that push) |
| `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` | Prior PE pin | 2026-06-04T17:25:50Z | `sha256:d398b4052539c6890f529b100defda9c52d1f5c9a9a736d4668f172e3264dec` |

**Recommended PE pin:** `taig2k/finance_app_for_aws:5175aa9f31ef9889b06df2043215b7c0837e08ba` (includes full P0 security bundle + CI fix).

---

## 7. Success Criteria

| Criterion | Status |
|-----------|--------|
| Security branch committed | **Pass** (`def52aa`) |
| Security branch pushed | **Pass** |
| Merged into `deployable` | **Pass** |
| Tests pass | **Pass** (local + CI on `5175aa9`) |
| Terraform validate passes | **Pass** |
| Docker publish succeeds | **Pass** (`5175aa9`) |
| New pinned image tag recorded | **Pass** (`5175aa9f31ef…`) |
| Report created | **Pass** (this file) |

---

## 8. Blockers

| ID | Blocker | Severity |
|----|---------|----------|
| — | None for artifact publish on `5175aa9` | — |
| B1 | `def52aa` image never published | **Resolved** by `5175aa9` republish |
| B2 | Terraform default `docker_image` still `89a4ea5…` | **Advisory** — update in ACI-PE-04 / tfvars when redeploying PE |
| B3 | PE instance still runs prior image | **Expected** — out of PA-04 scope |
| B4 | `config.json` Windows key path breaks CI preflight without `OPENAI_API_KEY` | **Mitigated** in workflows; consider `config.docker.example.json` for CI long-term |

---

## 9. Artifact Ready for ACI-PE-04?

**Yes.** Use Docker pin:

`taig2k/finance_app_for_aws:5175aa9f31ef9889b06df2043215b7c0837e08ba`

PE validation should cover: Gunicorn entrypoint, CSRF on POST routes, `debug=False`, SSM key path (after Terraform apply on instance), SSH/tfvars constraints. **Do not declare PAPE** until PE-04/PE-05 complete.

---

## Scope Compliance

- [x] Merge and push only (no Terraform apply, no EC2, no PAPE)
- [x] CI + Docker Publish verified on publishable commit
- [x] Image tags documented
- [x] Report path: `reports/aci_pa/aci_pa_04_security_remediation_artifact_publish.md`
