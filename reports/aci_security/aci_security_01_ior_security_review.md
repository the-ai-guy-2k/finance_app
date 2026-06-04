# ACI-SECURITY-01 — IOR Security Review

**Project:** Financial App (Financial Nebula Node)  
**Date:** 2026-06-04  
**Scope:** Assessment only — no remediation, no AWS/Terraform/code changes, no PAPE  
**Environment reviewed:** SPE-01 PE (`i-0b68a04f4d3aa5ab9`, http://44.197.147.63) + `deployable` codebase and CI/CD

---

## Executive Summary

The IOR release candidate is **appropriate for a controlled demonstration PE** when operators accept explicit caveats. It is **not ready for production approval (PAPE)** without substantial security hardening.

**Overall security score:** **4.8 / 10** (demo PE posture)

| Context | Verdict |
|---------|---------|
| SPE-01 demo / IOR validation | **Acceptable with documented risks** |
| PAPE / production declaration | **Blocked** by multiple HIGH findings |
| Proceed to ACI-PE-03 | **Yes** (governance pass with security caveats) |

**Evidence basis:** Repository review, Terraform SPE-01 configuration, Docker/CI workflows, PE-01/PE-02 reports. No live penetration test or AWS API audit performed in this ACI.

---

## Architecture Reviewed

| Layer | Components |
|-------|------------|
| Application | Flask MVP, JSON file storage, OpenAI receipt + insights |
| Container | `python:3.12-slim`, `CMD python app.py`, runtime-mounted config |
| CI/CD | GitHub Actions `ci.yml`, `docker-publish.yml` → Docker Hub |
| PE | Single EC2 (AL2023), Docker, systemd `financial-app`, SG HTTP+SSH |
| Secrets | `OPENAI_API_KEY` env, Terraform sensitive var → user-data, GitHub Docker secrets |

---

## A. Secrets

| Finding ID | Severity | Finding | Release impact |
|------------|----------|---------|----------------|
| SEC-A01 | **HIGH** | OpenAI API key stored on instance at `/opt/financial-app/env` (mode 600) and injected into container via `EnvironmentFile`. Compromise of EC2 or container yields key theft. | **Blocks PAPE**; acceptable for demo with rotation plan |
| SEC-A02 | **HIGH** | OpenAI key embedded in EC2 **user-data** via Terraform `base64encode(var.openai_api_key)`. Visible to principals with `ec2:DescribeInstanceAttribute` / state access; may persist in **local Terraform state** if applied with key. | **Blocks PAPE** |
| SEC-A03 | **MEDIUM** | Flask `secret_key` in PE bootstrap config is a **static demo value** (`spe01-demo-secret-change-if-reused` in `user_data.sh`). Weak session signing if sessions used. | Non-blocking for demo |
| SEC-A04 | **LOW** | Local dev fallback secret documented in `aci.md` (`theaiguyfreakout`); `app/__init__.py` defaults to config or fallback pattern. Not used in SPE-01 bootstrap if config mounted correctly. | Informational |
| SEC-A05 | **INFORMATIONAL** | GitHub Actions Docker Hub credentials use repository secrets (`DOCKERHUB_*`) — appropriate pattern; not in repo. | Positive |
| SEC-A06 | **INFORMATIONAL** | `.gitignore` excludes `terraform.tfvars`, `*.pem`, `.env`, keys — appropriate. | Positive |

**OpenAI integration:** Key loading prioritizes `OPENAI_API_KEY` env (`app/utils/openai_key.py`). Receipt images are **base64-sent to OpenAI** (third-party processing) — data leaves the instance.

---

## B. Application

| Finding ID | Severity | Finding | Release impact |
|------------|----------|---------|----------------|
| SEC-B01 | **CRITICAL** | **No authentication or authorization** on any route. Any internet client reaching port 80 can read transactions, upload receipts, trigger insights (cost), and **demo reset** (data destruction). | **Blocks PAPE** |
| SEC-B02 | **HIGH** | `app.py` runs Flask with **`debug=True`** and `host='0.0.0.0'`. Docker `CMD ["python", "app.py"]` uses this entrypoint — Werkzeug debugger exposure risk if errors trigger debug mode on internet-facing host. | **Blocks PAPE** |
| SEC-B03 | **MEDIUM** | File uploads validate **extension and size** only (`secure_filename`); no content sniffing. Malicious file upload to `uploads/` possible (stored on persistent volume). | Non-blocking for demo; document |
| SEC-B04 | **MEDIUM** | **No CSRF protection** on POST routes (`add_transaction`, `upload_receipt`, `demo_reset`). Combined with SEC-B01, any site can trigger actions via victim browser. | **Blocks PAPE** if public URL; demo caveat |
| SEC-B05 | **MEDIUM** | Preflight failures render **`error.html`** with error strings (may include config paths). Information disclosure on misconfiguration. | Non-blocking when healthy |
| SEC-B06 | **MEDIUM** | Logs may include **OpenAI response previews** (up to 500 chars) on JSON parse failure (`openai_receipt_service.py`) — receipt/financial data in `logs/app.log`. | Non-blocking; restrict log access |
| SEC-B07 | **LOW** | CSV upload parses arbitrary user CSV into transactions — formula injection risk if exported to Excel elsewhere. | Non-blocking |
| SEC-B08 | **INFORMATIONAL** | Jinja2 templates use default auto-escaping for `{{ }}` — reduces XSS risk for reflected fields. | Positive |
| SEC-B09 | **INFORMATIONAL** | Upload max 10 MB; allowed receipt formats whitelist — basic abuse limit. | Positive |

**Receipt handling:** Uploaded files saved under `uploads/`; sent to OpenAI Vision API; transactions persisted to `data/transactions.json` on mounted volumes in PE.

---

## C. Container

| Finding ID | Severity | Finding | Release impact |
|------------|----------|---------|----------------|
| SEC-C01 | **HIGH** | **`docker_image` default and SPE-01 bootstrap use `:latest`**. PE-01 proved stale local `latest` can serve **wrong build** (pre-hardening). Supply-chain / consistency risk. | Non-blocking if SHA pinned at ops; **blocks PAPE** if unpinned |
| SEC-C02 | **MEDIUM** | Image `FROM python:3.12-slim` without digest pin; `COPY . ./` — `.dockerignore` excludes secrets/config but **not** `terraform/`, `reports/`, `.git` is excluded. Image bloat and accidental file inclusion risk on build context changes. | Non-blocking |
| SEC-C03 | **MEDIUM** | Container runs as **root** (default Docker) unless USER directive — not set in Dockerfile. | Non-blocking for demo |
| SEC-C04 | **INFORMATIONAL** | Runtime mount of config only; API key via env not baked in image build — good practice. | Positive |
| SEC-C05 | **INFORMATIONAL** | Public image on Docker Hub `taig2k/finance_app_for_aws` — expected; verify account control for publishes. | Positive |

**Validated pin (PE-01):** `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` — recommended for PE operations.

---

## D. AWS

| Finding ID | Severity | Finding | Release impact |
|------------|----------|---------|----------------|
| SEC-D01 | **HIGH** | Security group allows **HTTP 80 from `0.0.0.0/0`** (default `http_allowed_cidrs`). World-readable web app. | **Blocks PAPE**; expected for SPE-01 demo |
| SEC-D02 | **HIGH** | Security group allows **SSH 22 from `0.0.0.0/0`** (default `ssh_allowed_cidrs`). Global SSH attack surface. | **Blocks PAPE**; restrict to operator IP |
| SEC-D03 | **HIGH** | **No TLS termination** (no ACM/ALB/HTTPS). Credentials and data in transit over HTTP. | **Blocks PAPE** |
| SEC-D04 | **MEDIUM** | **Public IPv4** on instance; IP changes on stop/start — no stable DNS/TLS in SPE-01 design. | Non-blocking for demo |
| SEC-D05 | **MEDIUM** | Egress **0.0.0.0/0** all protocols — required for OpenAI/Docker Hub; broad exfil path if compromised. | Accept for MVP |
| SEC-D06 | **INFORMATIONAL** | EBS root volume **`encrypted = true`** — positive. | Positive |
| SEC-D07 | **INFORMATIONAL** | **IMDSv2 required** (`http_tokens = "required"`) — reduces SSRF metadata theft risk. | Positive |
| SEC-D08 | **INFORMATIONAL** | No SSM Session Manager observed (PE-01); SSH-only operator access. | Informational |

---

## E. Data

| Finding ID | Severity | Finding | Release impact |
|------------|----------|---------|----------------|
| SEC-E01 | **HIGH** | Financial transactions and uploads persist on **instance EBS** without encryption-at-rest beyond EBS default; **no backup** or retention policy in scope. | **Blocks PAPE** |
| SEC-E02 | **MEDIUM** | **Demo reset** deletes transactions, uploads, logs — good for demos; **no auth** means anyone can wipe data (SEC-B01). | Tied to SEC-B01 |
| SEC-E03 | **MEDIUM** | Receipt images may contain **PII**; stored locally and transmitted to OpenAI — privacy/compliance not addressed. | Document for stakeholders |
| SEC-E04 | **LOW** | No data classification or access audit trail. | Non-blocking |
| SEC-E05 | **INFORMATIONAL** | Data volumes mounted into container (`/app/data`, `/app/uploads`, `/app/logs`) — clear persistence boundary. | Positive |

---

## Findings Summary by Severity

### CRITICAL (1)

| ID | Title |
|----|-------|
| SEC-B01 | No authentication — full app exposed to internet |

### HIGH (9)

| ID | Title |
|----|-------|
| SEC-A01 | OpenAI key on instance filesystem / container env |
| SEC-A02 | OpenAI key in Terraform user-data / state exposure |
| SEC-B02 | Flask `debug=True` in production container entrypoint |
| SEC-D01 | HTTP open to world (0.0.0.0/0) |
| SEC-D02 | SSH open to world (0.0.0.0/0) |
| SEC-D03 | No TLS / HTTPS |
| SEC-C01 | `:latest` image tag / stale deploy risk |
| SEC-E01 | Sensitive data on single EC2 without production controls |

### MEDIUM (10)

SEC-A03, SEC-B03, SEC-B04, SEC-B05, SEC-B06, SEC-C02, SEC-C03, SEC-D04, SEC-D05, SEC-E02, SEC-E03

### LOW (2)

SEC-A04, SEC-B07, SEC-E04

### INFORMATIONAL (7)

SEC-A05, SEC-A06, SEC-B08, SEC-B09, SEC-C04, SEC-C05, SEC-D06, SEC-D07, SEC-D08, SEC-E05

---

## Release-Blocking Findings (PAPE)

These should **block Production Approval / PAPE** until remediated or explicitly waived by governance with compensating controls:

1. **SEC-B01** — No authentication on internet-facing app  
2. **SEC-B02** — Flask debug mode in container entrypoint  
3. **SEC-D01** + **SEC-D03** — World HTTP without TLS  
4. **SEC-D02** — World SSH  
5. **SEC-A01** + **SEC-A02** — API key exposure surfaces (disk, user-data, state)  
6. **SEC-E01** — No production-grade data protection  
7. **SEC-B04** — CSRF + anonymous destructive actions (demo reset)  
8. **SEC-C01** — Unpinned image / wrong-version deploy (operational security)

**Count:** 8 thematic blockers (10+ finding IDs).

---

## Non-Blocking Findings (IOR demo PE)

Acceptable for **SPE-01 demonstration** with operator acknowledgment:

- SEC-D01/D03 as **documented demo-only HTTP**
- SEC-C01 if operators **pin SHA** on boot (PE-01 procedure)
- SEC-B03/B05/B06/B07 — upload/logging hardening backlog
- SEC-A03 demo Flask secret
- SEC-D04 ephemeral IP
- Transaction edit/delete absence (product, not security)

---

## Remediation Recommendations (Not Performed)

| Priority | Recommendation |
|----------|----------------|
| P0 | Set `debug=False` for production; use gunicorn/waitress in Docker |
| P0 | Add authentication (at minimum HTTP basic or OAuth) before PAPE |
| P0 | Restrict SG: HTTP/SSH to operator CIDRs; add TLS (ALB+ACM or reverse proxy) |
| P0 | Pin Docker image by digest/SHA in Terraform and systemd |
| P1 | Remove API key from user-data; use SSM Parameter Store / Secrets Manager + instance role |
| P1 | Rotate OpenAI key; restrict key scope/billing alerts |
| P1 | Add CSRF tokens for all state-changing forms |
| P2 | Content-type validation on uploads; scan or sandbox uploads |
| P2 | Reduce log sensitivity (no receipt previews in logs) |
| P2 | Harden Dockerfile: non-root USER, pin base image digest |
| P3 | WAF/rate limiting; SSM instead of SSH |

---

## GitHub Actions Security Notes

| Item | Assessment |
|------|------------|
| Docker publish on `deployable` only | Appropriate |
| Secrets via GitHub encrypted secrets | Appropriate |
| Tests before publish | Appropriate |
| Public repo | Source and workflow visible — expected |
| No OIDC to AWS in workflows | N/A for current SPE-01 (manual Terraform) |

---

## Should PAPE Be Blocked by Security?

**Yes — PAPE should remain blocked.**

Security posture is **inconsistent with production approval** for an internet-exposed financial application handling uploads and third-party AI processing. **IOR operational readiness (PE-02) does not override** these blockers.

**PAPE may be discussed only after:**

- ACI-PE-03 governance sign-off **with security caveats**, and  
- Either remediation of P0 items or **formal risk acceptance** documented by DWN for a **demo-only** boundary (not general production).

---

## Recommendation for ACI-PE-03

1. Record **security acceptance statement** for SPE-01: demo-only, no PAPE, known blockers listed above.  
2. Confirm PE still uses **pinned image** `89a4ea50348c73a8fcaf47c95ad7fb24a803d16d`.  
3. Re-run `scripts/pe01_validate.py`; optionally verify **debug is not externally exploitable** (manual check).  
4. Document **operator obligations:** restrict SG CIDRs when possible, rotate keys, stop instance when idle.  
5. Do **not** declare PAPE in PE-03 unless governance explicitly overrides security blockers.

---

## Scope Compliance

- [x] Architecture reviewed
- [x] Findings documented and categorized
- [x] Release blockers identified
- [x] Report created
- [x] No remediation performed
- [x] No AWS / Terraform / code changes
- [x] PAPE not declared

---

## Sign-Off Position

| Question | Answer |
|----------|--------|
| Proceed to ACI-PE-03? | **Yes** |
| Block PAPE on security grounds? | **Yes** |
| Safe for controlled IOR demo on SPE-01? | **Yes, with caveats** |
