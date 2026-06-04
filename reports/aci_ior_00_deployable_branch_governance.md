# ACI-IOR-00 Deployable Branch Governance Report

**Report ID:** ACI-IOR-00  
**Timestamp:** 2026-06-03  
**Governance commit:** `9fbd19b` — ACI-IOR-00: establish deployable branch governance  
**Mission:** Establish `deployable` as protected release branch for IOR feature work

---

## Executive Summary

Local and remote release branch governance updated from **`main`** to **`deployable`**. GitHub Actions Docker publish now triggers on **`deployable`**. Tests pass. Remote **`main`** branch still exists — deletion recommended as a follow-up operator action on GitHub.

**Final status:** **ACHIEVED**

---

## Branch Transition

| Field | Value |
|-------|-------|
| **Old default branch (local)** | `main` |
| **New default branch (local)** | `deployable` |
| **HEAD commit** | `8d0118d` (includes PA, CI/CD, SPE-01 Terraform, Docker publish trigger) |
| **Stale local `deployable` removed** | Yes (was `9d258af`, superseded by `main` history) |

---

## Remote Verification

| Check | Command / Result |
|-------|------------------|
| Remote URL | `https://github.com/the-ai-guy-2k/finance_app.git` |
| Push `deployable` | `git push -u origin deployable` |
| Verify ref | `9fbd19ba65f17bb390140e36f656d9349e7e4556` → `refs/heads/deployable` |
| Remote `main` still exists | `8d0118dd11aec118a3dff2a614d3b351ac6e1dd3` (not deleted) |

---

## Workflow Trigger Updates

| File | Change |
|------|--------|
| `.github/workflows/docker-publish.yml` | `push.branches`: `main` → **`deployable`** |
| `.github/workflows/ci.yml` | Comment updated; still triggers on all `push` + `pull_request` (feature branch CI unchanged) |

---

## Docs Updated (Current-Path Only)

| File | Change |
|------|--------|
| `README.md` | Release branch references → `deployable` |
| `docs/DOCKER_USAGE.md` | Publish triggers → `deployable` |
| `docs/GOVERNANCE.md` | Docker governance → `deployable` |
| `docs/aiw_errors/README.md` | Pipeline flow → merge to `deployable` |
| `terraform/spe-01/terraform.tfvars.example` | Comment updated |

Historical reports under `reports/` (CI/CD-03, PA, etc.) **not modified** — they record past events accurately.

---

## Tests Result

```
19 passed in ~5s
```

**Pass** — no blockers.

---

## Security — `.gitignore` Confirmed

| Pattern | Present |
|---------|---------|
| `.env`, `*.env` | Yes |
| `terraform.tfvars`, `*.tfstate`, `.terraform/` | Yes |
| `*.pem` | Yes |
| `uploads/`, `logs/` | Yes |

---

## Remote `main` Branch Recommendation

| Action | Recommendation |
|--------|----------------|
| Delete `origin/main` now | **Not automatic** — report only |
| **Next operator steps on GitHub** | 1. Set **default branch** to `deployable` in repo Settings → Branches. 2. After verification, optionally delete `main` if no longer needed. 3. Confirm Docker Publish workflow runs on next push to `deployable`. |

Keeping both branches temporarily is safe; `deployable` is now the authoritative release line.

---

## Can We Proceed to ACI-IOR-01?

**Yes.**

Create feature branches from `deployable` for IOR work. Merge to `deployable` only after CI passes.

---

## Scope Compliance

- No application feature changes
- No OpenAI logic changes
- No Terraform / AWS actions
- PAPE not declared
