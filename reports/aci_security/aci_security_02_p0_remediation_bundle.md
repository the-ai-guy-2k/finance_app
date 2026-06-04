# ACI-SECURITY-02 — P0 Security Remediation Bundle

**Project:** Financial App  
**Branch:** `feature/pape-p0-security-remediation`  
**Date:** 2026-06-04  
**Scope:** Implement broke-mode P0 bundle (no auth, TLS, WAF, rate limiting)

---

## Executive Summary

All six P0 implementation items were completed in the **release artifact** (application, Docker, Terraform SPE-01). Local validation: **28 pytest passed**, `terraform validate` success, Gunicorn config check success.

**PE/AWS apply and live SPE-01 verification** are **not** part of this ACI — required for **ACI-PE-04**.

---

## Implemented Items

| # | Requirement | Status | Implementation |
|---|-------------|--------|----------------|
| 1 | Disable Flask debug | **Done** | `app.py`: `debug=False`; Docker uses Gunicorn not dev server |
| 2 | Gunicorn production server | **Done** | `gunicorn` in `requirements.txt`; `Dockerfile` CMD; `gunicorn.conf.py` |
| 3 | OpenAI key via AWS SSM | **Done** | `openai_key.py` boto3 SSM; Terraform SSM + IAM role; user-data no key |
| 4 | Restrict SSH CIDR | **Done** | `ssh_allowed_cidrs` validation blocks `0.0.0.0/0`; example `203.0.113.10/32` |
| 5 | Pin Docker image | **Done** | `docker_image` default SHA tag; validation rejects `:latest` |
| 6 | CSRF protection | **Done** | `CSRFProtect(app)`; tokens on all POST forms |

---

## Files Modified

| File | Change |
|------|--------|
| `app.py` | `debug=False` |
| `Dockerfile` | Gunicorn CMD |
| `gunicorn.conf.py` | **New** |
| `requirements.txt` | gunicorn, flask-wtf, boto3 |
| `app/__init__.py` | CSRFProtect |
| `app/utils/openai_key.py` | SSM loader (env → SSM → file) |
| `app/utils/preflight.py` | SSM in error message |
| `app/templates/*.html` | `csrf_token` on POST forms |
| `terraform/spe-01/main.tf` | IAM profile, hop limit 2, user-data vars |
| `terraform/spe-01/iam_ssm.tf` | **New** — SSM parameter, IAM role/policy, instance profile |
| `terraform/spe-01/variables.tf` | SSH validation, pinned image, SSM param name |
| `terraform/spe-01/user_data.sh` | SSM env only; no API key in user-data |
| `terraform/spe-01/terraform.tfvars.example` | Operator CIDR documentation |
| `terraform/spe-01/outputs.tf` | SSM name, docker_image outputs |
| `tests/test_csrf.py` | **New** |
| `tests/test_openai_key.py` | SSM mock test |
| `tests/test_demo_reset.py` | CSRF in route tests |
| `scripts/pe01_validate.py` | CSRF-aware POSTs + enforcement check |
| `.github/workflows/ci.yml` | py_compile openai_key, gunicorn.conf |

---

## Validation Results

| Check | Result |
|-------|--------|
| `pytest -v` | **28 passed** (~6.6s) |
| `terraform validate` (spe-01) | **Success** |
| `gunicorn --check-config app:app` | **Success** |
| `app.py` debug flag | **`debug=False`** |
| CSRF unit tests | **Pass** (400 without token; 200 with token) |
| SSM loader unit test | **Pass** (mocked boto3) |

### Not validated in this ACI (PE-04 scope)

| Check | Notes |
|-------|-------|
| Live SSM read on EC2 | Requires `terraform apply` + instance profile |
| SSH restriction in AWS | Requires apply with operator `ssh_allowed_cidrs` |
| Pinned image on running instance | Requires bootstrap / docker pull on PE |
| `pe01_validate.py` against live PE | Old image lacks CSRF until redeploy |

---

## Operator CIDR (SSH)

Documented in `terraform/spe-01/terraform.tfvars.example`:

```hcl
ssh_allowed_cidrs = ["203.0.113.10/32"]
```

**Operator must replace** `203.0.113.10/32` with their actual public egress IP before `terraform apply`. Terraform **rejects** `0.0.0.0/0` for SSH.

---

## OpenAI Key Flow (Post-Remediation)

1. **Apply time:** `TF_VAR_openai_api_key` → Terraform creates SSM **SecureString** (not user-data).
2. **Bootstrap:** `/opt/financial-app/env` sets `OPENAI_SSM_PARAMETER_NAME` and `AWS_REGION` only.
3. **Container:** App calls `boto3` SSM `GetParameter` with decryption (instance profile + hop limit 2).
4. **Local dev:** `OPENAI_API_KEY` or `openai.api_key_file` still supported.

---

## Pinned Docker Image

Default (until next publish after merge):

```
taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d
```

After merge to `deployable`, update default to new `${{ github.sha }}` tag from Docker Publish workflow.

---

## Blockers

| ID | Blocker | Owner |
|----|---------|-------|
| B1 | Existing SPE-01 needs **terraform apply** + new image deploy for live P0 | Operator / PE-04 |
| B2 | Operator must set real **ssh_allowed_cidrs** in `terraform.tfvars` | Operator |
| B3 | `terraform.tfvars` on operator machine may still have `0.0.0.0/0` — plan will fail validation | Operator fix |

---

## Remaining Security Findings (Post-P0)

Still **out of scope** for this bundle (per ACI):

| ID | Finding | Severity |
|----|---------|----------|
| R1 | No authentication / authorization | CRITICAL |
| R2 | No HTTPS / TLS | HIGH |
| R3 | HTTP 0.0.0.0/0 still allowed | HIGH (demo) |
| R4 | No rate limiting / WAF | MEDIUM |
| R5 | Container runs as root | MEDIUM |
| R6 | Upload content-type not sniffed | MEDIUM |

These **still block PAPE** until addressed or formally waived for demo-only scope.

---

## Recommendation for ACI-PE-04

1. Merge `feature/pape-p0-security-remediation` → `deployable`; confirm Docker publish for new SHA.
2. Update `terraform.tfvars`: operator `ssh_allowed_cidrs`, pinned `docker_image` = new SHA.
3. `terraform apply` (or targeted instance refresh) with `TF_VAR_openai_api_key` to populate SSM.
4. Restart `financial-app.service` on SPE-01 (or replace instance if user-data change required).
5. Run `scripts/pe01_validate.py` against live URL — expect **csrf_enforced** PASS on new image.
6. Confirm SSH from operator IP works; confirm SSH from other IPs **fails**.
7. Document results in `aci_pe_04_pe_regression_post_remediation.md`.

---

## Scope Compliance

- [x] Debug disabled
- [x] Gunicorn active (container entrypoint)
- [x] OpenAI key from SSM (application + Terraform)
- [x] SSH restricted (Terraform validation)
- [x] Image pinned (no `:latest`)
- [x] CSRF enabled
- [x] Local validation completed
- [x] Report created
- [x] No auth, TLS, WAF (per scope)
- [x] PE-04 not performed
