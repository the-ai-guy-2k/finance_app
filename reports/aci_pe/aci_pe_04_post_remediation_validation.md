# ACI-PE-04 — Post-Remediation PE Deployment + Validation

**Project:** Financial App  
**Date:** 2026-06-04  
**Scope:** Deploy remediated image to SPE-01, validate security + functionality (no PAPE declaration)  
**Pinned image:** `taig2k/finance_app_for_aws:5175aa9f31ef9889b06df2043215b7c0837e08ba`

---

## Executive Summary

Terraform was applied to update SPE-01 with the **5175aa9** security-remediation image, **SSH restricted** to operator CIDR `76.122.33.89/32`, and **SSM SecureString** created for the OpenAI key. The first apply **partially failed** (`iam:CreateRole` denied for user `nebula`) after the prior instance was terminated; a **recovery apply** recreated the instance without IAM instance profile, using **bootstrap `OPENAI_API_KEY` env** (app precedence: env before SSM).

**Functional validation:** `scripts/pe01_validate.py` — **OVERALL: PASS** (8/8). **Gunicorn** active, **pinned image** confirmed, **CSRF** enforced. **SSM from container:** **not verified** (IAM profile blocked); SSM parameter **exists** in AWS; runtime key via env.

**PAPE:** Not declared (per scope).

---

## 1. AWS Identity

| Field | Value |
|-------|--------|
| Profile | `nebula` |
| Account | `526123657916` |
| ARN | `arn:aws:iam::526123657916:user/nebula` |

---

## 2. Instance State

| Field | Before PE-04 | After PE-04 |
|-------|----------------|-------------|
| Instance ID | `i-0b68a04f4d3aa5ab9` | `i-0055c22499e9b2853` |
| State | running | **running** |
| Public IP | `44.197.147.63` | **`44.192.97.51`** |
| AMI | `ami-074bb5e3c681b0735` | same family (AL2023) |

**Note:** Instance replacement occurred due to `user_data_replace_on_change` and failed mid-apply; recovery recreated SPE-01 on the same security group and Terraform workspace.

---

## 3. Terraform Plan Summary (initial)

| Action | Resource |
|--------|----------|
| **Create** | SSM parameter, IAM role, IAM policy, instance profile |
| **Update in-place** | Security group (SSH CIDR) |
| **Replace** | EC2 instance (user_data / IAM / metadata) |

**tfvars updates:**

- `docker_image` → `taig2k/finance_app_for_aws:5175aa9f31ef9889b06df2043215b7c0837e08ba`
- `ssh_allowed_cidrs` → `["76.122.33.89/32"]` (operator egress; not `0.0.0.0/0`)
- `enable_ec2_iam_ssm` → `false` (recovery; see §4)

---

## 4. Terraform Apply Result

### First apply (saved plan `tfplan`)

| Step | Result |
|------|--------|
| SSM parameter `/financial-app/spe-01/openai_api_key` | **Created** |
| Security group SSH rule | **Updated** (`76.122.33.89/32`) |
| Instance `i-0b68a04f4d3aa5ab9` | **Destroyed** |
| IAM role `financial-app-spe-01-ec2-role` | **Failed** — `AccessDenied: iam:CreateRole` |

### Recovery apply

| Step | Result |
|------|--------|
| Instance `i-0055c22499e9b2853` | **Created** |
| IAM resources | **Skipped** (`enable_ec2_iam_ssm = false`) |
| Bootstrap | `OPENAI_API_KEY` via user-data env file (not printed) |

**Final apply:** `Resources: 1 added` — **success**.

---

## 5. Public IP / App URL

| Item | Value |
|------|--------|
| **App URL** | http://44.192.97.51 |
| **SSH** | `ssh -i <gina.pem> ec2-user@44.192.97.51` |

---

## 6. SSH Restriction Result

| Check | Result |
|-------|--------|
| SG ingress port 22 | **`76.122.33.89/32` only** |
| `0.0.0.0/0` on SSH | **Removed** |
| HTTP port 80 | `0.0.0.0/0` (unchanged; demo scope) |

---

## 7. SSM Validation Result

| Check | Result |
|-------|--------|
| Parameter exists | **Pass** — `/financial-app/spe-01/openai_api_key` (SecureString, version 1) |
| IAM instance profile on EC2 | **Not attached** — `nebula` user lacks `iam:CreateRole` |
| Container reads key via SSM | **Not verified** — `OPENAI_API_KEY` present in container env (bootstrap fallback); `load_openai_api_key()` uses env first |
| AI insights / receipt parse | **Pass** (implies key available at runtime) |

**PE-04 SSM criterion:** **Partial** — secret stored in SSM; end-to-end SSM-from-instance requires IAM permissions or admin-created role + `enable_ec2_iam_ssm = true` re-apply.

---

## 8. Running Image Result

| Check | Result |
|-------|--------|
| `docker ps` image | `taig2k/finance_app_for_aws:5175aa9f31ef9889b06df2043215b7c0837e08ba` |
| Matches PA-04 pin | **Yes** |
| `financial-app.service` | **active** |

---

## 9. Gunicorn / Debug Result

| Check | Result |
|-------|--------|
| Process | `gunicorn -c gunicorn.conf.py app:app` (master + workers) |
| Flask dev server | **Not used** in container |
| `app.py` entry | `debug=False` in codebase / image |

---

## 10. CSRF Result

| Check | Result |
|-------|--------|
| `pe01_validate.py` `csrf_enforced` | **PASS** — bare POST → HTTP 400 |
| Forms with token | Transaction, receipt, demo reset **PASS** |

---

## 11. App Validation Results (`scripts/pe01_validate.py`)

**Command:** `python scripts/pe01_validate.py http://44.192.97.51`

| Test | Result |
|------|--------|
| reachability | **PASS** |
| dashboard | **PASS** |
| transaction | **PASS** |
| receipt_upload | **PASS** |
| ai_insights | **PASS** |
| demo_reset | **PASS** |
| post_reset_usability | **PASS** |
| csrf_enforced | **PASS** |
| **OVERALL** | **PASS** |

---

## 12. Remaining Blockers

| ID | Blocker | Severity |
|----|---------|----------|
| B1 | IAM `CreateRole` denied for `nebula` — no instance profile; SSM not used from container | **High** for full P0-3 SSM path |
| B2 | OpenAI key in bootstrap user-data when `enable_ec2_iam_ssm=false` | **Medium** — works but less ideal than SSM-only |
| B3 | No authentication / TLS | **PAPE** — unchanged |
| B4 | Ephemeral public IP changed again | **Low** — update bookmarks / outputs |
| B5 | Prior instance `i-0b68a04f4d3aa5ab9` terminated during failed apply | **Resolved** — new instance operational |

---

## 13. Success Criteria

| Criterion | Status |
|-----------|--------|
| Terraform plan reviewed | **Pass** |
| Terraform apply succeeds | **Pass** (recovery apply) |
| SSH restricted | **Pass** |
| SSM secret path works | **Partial** (parameter yes; instance SSM read no) |
| Pinned image deployed | **Pass** |
| Gunicorn active | **Pass** |
| Debug disabled | **Pass** |
| CSRF validated | **Pass** |
| App functions validated | **Pass** |
| Report created | **Pass** |

---

## 14. Recommendation for ACI-PE-05

1. **Grant IAM** to deployer (or pre-create `financial-app-spe-01-ec2-role` + instance profile with `ssm:GetParameter` on `/financial-app/spe-01/openai_api_key`), set `enable_ec2_iam_ssm = true`, re-apply to attach profile and remove bootstrap key from user-data.
2. **Re-run PE validation** after SSM-only path: confirm container has no `OPENAI_API_KEY` env and receipt/insights still pass.
3. **PAPE re-evaluation:** SECURITY-02 + PE-04 evidence — expect **still DEFERRED** until auth/TLS and SSM-from-instance are closed; document residual risks (world HTTP, anonymous demo reset).
4. **Update** `scripts/pe01_validate.py` default BASE URL to `http://44.192.97.51` (optional hygiene).
5. **Do not declare PAPE** until PE-05 checklist complete.

---

## Scope Compliance

- [x] Updated existing SPE-01 (no new PE environment)
- [x] Pinned remediated image deployed
- [x] Validation script executed
- [x] No PAPE declaration
- [x] No new auth/HTTPS features
