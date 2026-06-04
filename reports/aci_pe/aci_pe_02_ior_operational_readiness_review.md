# ACI-PE-02 — IOR Operational Readiness Review

**Project:** Financial App (Financial Nebula Node)  
**Date:** 2026-06-04  
**Role:** Release manager assessment (evidence synthesis)  
**Scope:** Assessment only — no code, AWS, Terraform, PAPE, or security remediation  
**Mission progress:** IOR 6/9 ACIs complete through PE-01

---

## Executive Summary

The **Initial Official Release (IOR) candidate is operationally ready for security review and final release governance**, with **documented conditions**. Core business workflows validated in SPE-01 after deploying pinned image `taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d`. **PAPE must not be declared** until ACI-SECURITY-01 and ACI-PE-03 complete.

**Operational readiness score:** **8.2 / 10** — **READY WITH CONDITIONS**

| Dimension | Score (1–10) | Notes |
|-----------|--------------|-------|
| Feature completeness (IOR core) | 9.0 | PE-validated flows pass |
| Deployable / CI / artifact | 9.0 | Merge, tests, Docker publish verified |
| PE fidelity | 7.5 | Required manual image pin; stale `:latest` on boot |
| Operability / runbook | 6.5 | IP drift, PEM issue, no pinned bootstrap |
| Security / compliance | N/A | Deferred to ACI-SECURITY-01 |
| Documentation traceability | 7.0 | IOR-01 spec file not present on `deployable` tree |

---

## Evidence Reviewed

| ACI | Artifact | Key finding |
|-----|----------|-------------|
| **ACI-IOR-00** | `reports/aci_ior_00_deployable_branch_governance.md` | `deployable` is release branch; Docker publish on `deployable` |
| **ACI-IOR-01** | Release definition (per IOR-02/PA-02 references; `docs/nebula/ior/financial_app_ior_v1.md` cited in prior work, **not on current workspace tree**) | Defined IOR scope, GVC intent, gaps (e.g. demo reset, edit/delete) |
| **ACI-IOR-02** | `reports/aci_ior_02_hardening_bundle_report.md` | Demo reset, OpenAI env alignment, SDK v1 insights; 25 tests pass |
| **ACI-PA-02** | `reports/aci_pa_02_merge_hardening_to_deployable.md` | Fast-forward merge to `deployable`; no conflicts |
| **ACI-PA-03** | `reports/aci_pa/aci_pa_03_docker_artifact_verification.md` | Docker Publish success; SHA tags on Hub |
| **ACI-PE-01** | `reports/aci_pe/aci_pe_01_ior_operational_validation.md` | All IOR PE checks **PASS** after pinned image |

**Current deployment truth (PE-01):**

| Item | Value |
|------|-------|
| Instance | `i-0b68a04f4d3aa5ab9` (running at validation time) |
| App URL | http://44.197.147.63 (IP ephemeral) |
| Validated image | `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` |
| `deployable` tip at PE-01 report | `89a4ea5` (+ later docs commits) |

---

## A. Operational Strengths

1. **End-to-end IOR flows work in production (SPE-01)** after correct image deployment: dashboard, manual transactions, receipt upload path, OpenAI insights (non-heuristic), demo reset with post-reset usability.
2. **Release branch discipline:** `deployable` carries merged IOR hardening; CI and Docker Publish workflows succeeded for merge commits.
3. **Traceable artifacts:** Docker Hub tags match full Git SHAs (`3541fc2…`, `89a4ea5…`); GitHub Actions run IDs documented (PA-03).
4. **Automated quality gate:** 25 pytest tests pass locally and in CI; PE-01 added `scripts/pe01_validate.py` for repeatable HTTP validation.
5. **IOR hardening delivered:** Demo Reset (confirmed UI), standardized `OPENAI_API_KEY` loading, receipt + insights on modern OpenAI SDK patterns.
6. **OpenAI integration operational in PE:** Key present on instance; insights returned behavioral analysis text.
7. **Infrastructure exists and is reusable:** SPE-01 EC2 + SG + EBS; stop/start validated; no destroy required for demos.
8. **Governance alignment:** PA achieved; Docker artifact achieved; PE validated per checklist.

---

## B. Operational Weaknesses

1. **Image drift on instance restart:** Bootstrap/systemd defaulted to `taig2k/finance_app_for_aws:latest` with **stale local cache** — PE boot served **pre-hardening** app until manual pull/pin (PE-01 B2).
2. **`latest` tag ambiguity:** Docker Hub `latest` may not equal `deployable` tip SHA (PA-03 N1); Terraform/user-data still reference `:latest`.
3. **Ephemeral public IP:** Stop/start changes IP (`98.92.209.167` → `44.197.147.63`); breaks bookmarks and stale `terraform output` references.
4. **Operator SSH friction:** `gina.pem` stored as single-line PEM blocked SSH until reformat (PE-01 B3).
5. **PE-01 receipt evidence:** Upload returned 200 with minimal test PNG; **live merchant/amount parsing quality** not exhaustively scored in PE (unit tests mock OpenAI).
6. **CSV upload not re-run in PE-01 script:** Feature exists in app but not in automated PE validation set.
7. **Transaction edit/delete absent:** Identified in IOR-01 / IOR-02 as product gap; not required for PE-01 pass but limits “full” financial ops.
8. **Goals:** `goals.json` unused; hardcoded default goals only — limited goal-correlation value.
9. **IOR-01 specification file missing locally:** Reduces single-repo audit trail for Intent/GVC text (may exist on remote branch only).

---

## C. Known Risks

| ID | Risk | Likelihood | Impact | Mitigation (operational) |
|----|------|------------|--------|---------------------------|
| K1 | Wrong image after EC2 restart | High | High | Pin SHA in systemd/Terraform; pull on boot |
| K2 | HTTP-only exposure (no TLS) | Certain | Medium | Document demo-only; SECURITY-01 |
| K3 | OpenAI key on instance disk | Certain | High | SECURITY-01; rotate if exposed |
| K4 | SSH open (port 22) + HTTP (80) | Certain | Medium | SECURITY-01; restrict SG if possible |
| K5 | Single point of failure (one EC2) | Certain | Medium | Accept for SPE-01 MVP PE |
| K6 | No automated PE regression in CI | Medium | Medium | Run `pe01_validate.py` after deploy |
| K7 | PAPE declared prematurely | Low | High | Block PAPE until SECURITY-01 + PE-03 |

---

## D. Unknown Risks

| ID | Risk | Why unknown |
|----|------|-------------|
| U1 | Real receipt parsing accuracy on diverse receipts | PE used 1×1 PNG; not production receipt corpus |
| U2 | OpenAI rate limits / cost at demo scale | Not load-tested |
| U3 | EBS/data persistence edge cases | Demo reset clears app data; backup policy unclear |
| U4 | GitHub `main` vs `deployable` confusion | Remote `main` may still exist (IOR-00 note) |
| U5 | Container behavior after unpinned reboot | Not re-validated in PE-02 without new start test |
| U6 | Security posture (IAM, patching, secrets rotation) | ACI-SECURITY-01 not yet run |

---

## E. Release Risks

1. **Demonstrating on stale image** undermines IOR story (experienced in PE-01).
2. **Declaring PAPE before security review** would overstate production readiness.
3. **Relying on `latest` for SPE-01 bootstrap** desynchronizes PE from `deployable` SHA.
4. **Missing IOR-01 doc in repo** weakens audit defense for “what was promised vs delivered.”
5. **Feature scope creep expectations** (edit/delete, persistent goals) if stakeholders read full IOR-01 intent without gap list.

---

## Release Blockers vs Non-Blocking Issues

### Should block PAPE / final release declaration

| Item | Rationale |
|------|-----------|
| **ACI-SECURITY-01 not complete** | HTTP, SSH, secrets handling unreviewed |
| **ACI-PE-03 not complete** | Final PE governance pass not done |
| **PAPE explicitly not declared** | By program state |
| **No formal security sign-off** | Required before production declaration |

### Should NOT block progression to ACI-SECURITY-01

| Item | Rationale |
|------|-----------|
| Transaction edit/delete | Documented post-IOR / P1 gap |
| CSV not in PE-01 script | Feature exists; add to PE-03 regression |
| `goals.json` unused | MVP limitation; disclosed |
| `latest` vs SHA drift | Operational runbook fix, not functional blocker |
| Missing local IOR-01 file | Process/doc gap; restore from `feature/ior-release-definition` if needed |
| Public IP change | Expected EC2 behavior |

---

## IOR Intent Evaluation

**IOR intent (synthesized from program ACIs, MVP definition, and PE validation):**

Deliver a demonstrable, behavior-aware financial operational intelligence MVP that works in the **deployable → Docker → SPE-01** path, with core user journeys: view dashboard, capture transactions (manual + receipt), generate AI insights, and reset demo state for clean presentations.

| Intent element | Satisfied? | Evidence |
|----------------|------------|----------|
| Access deployed app | **Yes** | PE-01 HTTP 200 |
| Add transactions | **Yes** | PE-01 transaction PASS |
| Upload receipts | **Yes** | PE-01 receipt POST 200 |
| AI behavioral insights | **Yes** | PE-01 non-heuristic insights |
| Demo reset for presentations | **Yes** | PE-01 demo reset PASS |
| Release via `deployable` | **Yes** | PA-02, PA-03 |
| OpenAI in AWS | **Yes** | Key on instance; insights work |
| “Real thing” in AWS | **Yes** | SPE-01 validated (post pin) |

**Partial / not satisfied:**

| Element | Status |
|---------|--------|
| Transaction edit/delete | **No** (if in IOR-01 P0 — treat as **deferred**) |
| Persistent goals file | **Partial** (hardcoded defaults) |
| Zero-touch correct image on boot | **No** (manual pin required) |

**Conclusion — IOR intent:** **SUBSTANTIALLY SATISFIED** for Initial Official Release **demonstration and operational validation** purposes, with known deferred items documented.

---

## GVC Evaluation

**GVC (Governance Validation Criteria)** — release governance checklist derived from IOR-00, GOVERNANCE.md, CI/CD, and completed ACIs:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Release branch (`deployable`) established | **Pass** | IOR-00 |
| Feature work merged to `deployable` | **Pass** | PA-02 |
| CI passes on release branch | **Pass** | PA-02, PA-03 |
| Docker image published from `deployable` | **Pass** | PA-03 |
| Image traceable to commit SHA | **Pass** | PA-03 tags |
| PE exists (SPE-01) | **Pass** | DEVOPS-08 |
| PE operational validation | **Pass** | PE-01 (7/7 checks) |
| Tests (25) passing | **Pass** | IOR-02, PA-02 |
| Secrets not in git | **Pass** | Reports / tfvars gitignore |
| Security review | **Not started** | → ACI-SECURITY-01 |
| PAPE declaration | **Not done** | Correct state |
| Operator runbook for PE | **Partial** | PE-01 recommendations |

**Conclusion — GVC:** **PASS for operational and artifact governance**; **INCOMPLETE for security and final release declaration** (expected next ACIs).

---

## Operational Readiness Score

**8.2 / 10 — READY WITH CONDITIONS**

| Tier | Definition | This release |
|------|------------|--------------|
| 9–10 | Production-declared, security-signed | **No** (PAPE N/A) |
| 7–8 | Operationally demo-ready with documented caveats | **Yes** |
| &lt;7 | Material functional gaps in PE | **No** (after image pin) |

---

## Single Source of Truth — What Is Actually True

| Statement | True? |
|-----------|-------|
| IOR hardening is on `deployable` | **Yes** |
| Docker images exist for hardening commits | **Yes** |
| SPE-01 can run the IOR app end-to-end | **Yes** (with pinned image) |
| SPE-01 auto-serves latest IOR on cold start | **No** (without operator pull/pin) |
| All IOR-01 doc artifacts are in workspace | **Uncertain** (`financial_app_ior_v1.md` missing locally) |
| PAPE is achieved | **No** |
| Security review is complete | **No** |
| Transaction edit/delete shipped | **No** |

---

## Recommendation for ACI-SECURITY-01

1. **Review SPE-01 surface:** HTTP:80, SSH:22, no TLS, public EC2 IP, security group rules.
2. **Secrets:** `OPENAI_API_KEY` in `/opt/financial-app/env` (mode 600), Terraform user-data injection history, Docker env exposure, log redaction.
3. **Supply chain:** Docker Hub image pinning vs `latest`; verify digest `sha256:6e2ffc5e…` for `89a4ea5` tag.
4. **Access control:** SSH key management (`gina.pem` format, storage, rotation); no SSM agent observed.
5. **Data:** Local JSON on EBS volumes; demo reset behavior; no encryption-at-rest review.
6. **IAM:** `nebula` user permissions used for EC2 (least privilege check).
7. **Produce findings list:** critical / high / medium; map each to **block PAPE** vs **accept for SPE-01 MVP demo PE**.
8. **Do not remediate in SECURITY-01** unless ACI scope says otherwise — assessment first.

---

## Recommendation for ACI-PE-03

- Re-run `scripts/pe01_validate.py` after any infrastructure change.
- Add CSV upload to regression script.
- Confirm image pin survives reboot (or document mandatory bootstrap step).
- Restore/commit `docs/nebula/ior/financial_app_ior_v1.md` on `deployable` if still authoritative.
- Stop instance per operator schedule after validation cycle (optional).

---

## Scope Compliance

- [x] Evidence reviewed
- [x] Risks identified
- [x] Readiness assessed
- [x] IOR intent evaluated
- [x] GVC evaluated
- [x] Report created
- [x] No code / AWS / Terraform changes
- [x] PAPE not declared
- [x] No security remediation performed

---

## Sign-Off Position

| Question | Answer |
|----------|--------|
| Move to ACI-SECURITY-01? | **Yes** |
| Declare PAPE now? | **No** |
| Is IOR operationally ready for final release review? | **Yes, with conditions** |
