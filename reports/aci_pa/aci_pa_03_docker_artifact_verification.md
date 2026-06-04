# ACI-PA-03 — Docker Artifact Verification

**Project:** Financial App  
**Date:** 2026-06-04  
**Scope:** Artifact verification only (no PE, Terraform apply, PAPE)  
**Release branch:** `deployable`  
**Deployable tip:** `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d`

---

## Executive Summary

Docker Publish workflows for both post-merge commits **completed successfully**. Docker Hub contains `latest` and full-SHA tags for `3541fc2` (IOR hardening) and `89a4ea5` (deployable tip). **No workflow failures** observed on `deployable` for these commits.

**Release artifact assessment:** **APPROVED** for PE validation. Use pin tag `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` for exact deployable tip, or `3541fc28d860aa071aa7fb0af49dbc66c06fcb09` for hardening-only parity; `latest` currently matches the `3541fc2` image digest (see note below).

---

## Commits Under Verification

| Short SHA | Full SHA | Message |
|-----------|----------|---------|
| `3541fc2` | `3541fc28d860aa071aa7fb0af49dbc66c06fcb09` | ACI-IOR-02: implement IOR hardening bundle |
| `89a4ea5` | `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` | ACI-PA-02: document IOR hardening merge to deployable |

Both pushed to branch **`deployable`**.

---

## GitHub Actions Evidence

Source: [GitHub Actions API](https://api.github.com/repos/the-ai-guy-2k/finance_app/actions/runs?branch=deployable) (public repo, 2026-06-04).

### Docker Publish (`docker-publish.yml`)

| Commit | Run ID | Status | Conclusion | Branch | Started (UTC) | Updated (UTC) | URL |
|--------|--------|--------|------------|--------|----------------|---------------|-----|
| `3541fc2` | **26968127505** | completed | **success** | deployable | 2026-06-04T17:25:08Z | 2026-06-04T17:25:58Z | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26968127505 |
| `89a4ea5` | **26968128906** | completed | **success** | deployable | 2026-06-04T17:25:09Z | 2026-06-04T17:25:55Z | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26968128906 |

### CI (`ci.yml`) — companion runs (same pushes)

| Commit | Run ID | Conclusion | URL |
|--------|--------|------------|-----|
| `3541fc2` | 26968127540 | **success** | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26968127540 |
| `89a4ea5` | 26968129184 | **success** | https://github.com/the-ai-guy-2k/finance_app/actions/runs/26968129184 |

### Workflow failure check

All four runs above: **success**. No failed or cancelled Docker Publish runs for `3541fc2` or `89a4ea5` on `deployable`.

### Deployable source verification

- Workflow `on.push.branches` includes **`deployable`** (`.github/workflows/docker-publish.yml`).
- Each run `head_branch` = `deployable`; `head_sha` matches the pushed commit.
- Images tagged with `${{ github.sha }}` per workflow definition.

---

## Docker Hub Evidence

**Repository:** `taig2k/finance_app_for_aws`  
**Hub:** https://hub.docker.com/r/taig2k/finance_app_for_aws/tags  

Source: Docker Hub API v2 tags (2026-06-04).

| Tag | Commit correspondence | Last pushed (UTC) | Manifest digest (index) |
|-----|----------------------|-------------------|-------------------------|
| `latest` | Same image as `3541fc2…` tag* | 2026-06-04T17:25:51Z | `sha256:e706f9887c6d966b36f6c77bae6c9b8f311428c7b54b8a77fe79372bf9e038cb` |
| `3541fc28d860aa071aa7fb0af49dbc66c06fcb09` | `3541fc2` | 2026-06-04T17:25:53Z | `sha256:e706f9887c6d966b36f6c77bae6c9b8f311428c7b54b8a77fe79372bf9e038cb` |
| `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` | `89a4ea5` (deployable tip) | 2026-06-04T17:25:50Z | `sha256:6e2ffc5efaea0f999cc4c29d06922c4e242c539ee5fe7f21ba6e100387858a31` |

\*Parallel publishes on the same push window: the `3541fc2` workflow completed slightly after `89a4ea5` and repointed **`latest`** to the `3541fc2` image. Application code in both images is identical except `89a4ea5` adds the PA-02 report file under `reports/`.

### Older deployable tags (context)

| Tag | Notes |
|-----|-------|
| `9fbd19ba65f17bb390140e36f656d9349e7e4556` | Pre-hardening deployable (`9fbd19b`) |
| `8d0118dd11aec118a3dff2a614d3b351ac6e1dd3` | Legacy `main` publish |

---

## Publish Verification Checklist

| Criterion | Result |
|-----------|--------|
| `deployable` triggered Docker Publish | **Pass** (2 runs) |
| Docker Publish succeeded | **Pass** |
| `latest` tag exists | **Pass** |
| Commit-specific tags exist | **Pass** (`3541fc2…`, `89a4ea5…`) |
| Tags map to deployable SHAs | **Pass** |
| Built from `deployable` branch | **Pass** (Actions `head_branch`) |
| No blocking workflow failures | **Pass** |

---

## Blockers

| ID | Blocker | Severity |
|----|---------|----------|
| — | None for artifact verification | — |
| N1 | `latest` ≠ deployable tip image (`89a4ea5`) | **Advisory** — pin SHA in PE or align `latest` on next push |
| N2 | SPE-01 user-data may reference `:latest` | **Advisory** — confirm bootstrap pulls intended tag in ACI-PE-01 |

---

## Release Artifact Assessment

**Status: READY for PE validation**

The IOR hardening application is published and traceable:

- Primary pin: `taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d`
- Hardening pin (same app code): `taig2k/finance_app_for_aws:3541fc28d860aa071aa7fb0af49dbc66c06fcb09`
- Floating: `taig2k/finance_app_for_aws:latest` → currently `3541fc2` image (includes hardening)

---

## Recommendation for ACI-PE-01

1. **Start SPE-01 EC2** (separate ACI; not in PA-03 scope).
2. **Pin image** to `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` in validation notes, or update Terraform/user-data to use that tag instead of `:latest` for reproducibility.
3. Run PE checklist: HTTP 200, dashboard, transaction entry, receipt upload/parse, insights, demo reset, `OPENAI_API_KEY` on instance.
4. Record public IP (may change after stop/start) and compare against prior apply report.

---

## Scope Compliance

- [x] Workflow verified
- [x] Docker publish verified
- [x] Image tags documented
- [x] Deployable source verified
- [x] Report created
- [x] No EC2 / Terraform / PAPE
