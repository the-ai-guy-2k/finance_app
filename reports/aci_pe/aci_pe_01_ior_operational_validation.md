# ACI-PE-01 — IOR Operational PE Validation

**Project:** Financial App  
**Date:** 2026-06-04  
**Scope:** SPE-01 operational validation only (no Terraform apply, no new AWS resources, no PAPE)  
**Pinned image:** `taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d`

---

## Executive Summary

SPE-01 EC2 **`i-0b68a04f4d3aa5ab9`** was started successfully. The application was initially reachable on a **stale local `:latest` image** (pre–IOR hardening). The container was updated on-instance to the **pinned release tag** without Terraform changes. After update, **all IOR operational checks passed** (dashboard, transactions, receipt upload, AI insights, demo reset).

**IOR operational:** **YES** (after pinned image deployment)

---

## Instance State

| Field | Value |
|-------|-------|
| **Instance ID** | `i-0b68a04f4d3aa5ab9` |
| **Name** | `financial-app-spe-01` |
| **Type** | `t3.micro` |
| **Region** | `us-east-1` |
| **State** | **running** |
| **Previous state** | stopped (ACI-DEVOPS-09) |
| **Public IP (this session)** | `44.197.147.63` |
| **Public DNS** | `ec2-44-197-147-63.compute-1.amazonaws.com` |
| **Prior public IP (ACI-DEVOPS-08)** | `98.92.209.167` (changed after stop/start) |
| **App URL** | http://44.197.147.63 |

**Start command:**

```powershell
aws ec2 start-instances --profile nebula --region us-east-1 --instance-ids i-0b68a04f4d3aa5ab9
aws ec2 wait instance-running --profile nebula --region us-east-1 --instance-ids i-0b68a04f4d3aa5ab9
```

---

## Deployed Image Verification

### Initial state (on boot)

| Check | Result |
|-------|--------|
| Running image | `taig2k/finance_app_for_aws:latest` (local cache from original bootstrap) |
| IOR hardening present | **No** — `/demo_reset` returned **404** |
| Source | systemd `financial-app.service` on instance |

### Remediation (in-scope operational update)

Pulled and restarted with pinned tag via SSH (no Terraform):

```bash
sudo docker pull taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d
sudo sed -i 's|taig2k/finance_app_for_aws:[^ ]*|taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d|g' /etc/systemd/system/financial-app.service
sudo systemctl daemon-reload
sudo systemctl restart financial-app.service
```

### Final state

| Check | Result |
|-------|--------|
| **Running image** | `taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d` |
| **Digest** | `sha256:6e2ffc5efaea0f999cc4c29d06922c4e242c539ee5fe7f21ba6e100387858a31` |
| **Container status** | Up (healthy HTTP 200) |
| **OpenAI key** | Present in `/opt/financial-app/env` and container env (value redacted) |

---

## Application Reachability

| Test | Result |
|------|--------|
| `GET http://44.197.147.63/` | **HTTP 200** (~4s after start with cached image; ~20s after pinned restart) |
| Response size (dashboard) | ~1804 bytes (post-update) |

---

## Validation Results

Automated script: `scripts/pe01_validate.py` against `http://44.197.147.63` (after pinned image).

| # | Capability | Result | Evidence |
|---|------------|--------|----------|
| 1 | Dashboard | **PASS** | HTTP 200; title "Financial Nebula Node" |
| 2 | Transaction entry | **PASS** | `PE01_Validation_Merchant` / $42.50 visible on dashboard |
| 3 | Receipt upload | **PASS** | POST `/upload_receipt` → 200 (1×1 PNG test image) |
| 4 | AI insights | **PASS** | GET `/insights` 200; **not** heuristic-only fallback |
| 5 | Demo reset | **PASS** | `/demo_reset` form present; POST with confirm cleared test merchant |
| 6 | Post-reset usability | **PASS** | `PE01_PostReset` transaction added after reset |

**Overall automated run:** **PASS** (7/7 checks)

### AI insights note

Insights page returned substantive content (status 200, `heuristic_only=False`). OpenAI key confirmed on instance. Full insight text not reproduced in this report (may contain user data).

---

## Evidence URLs

| Resource | URL |
|----------|-----|
| Dashboard | http://44.197.147.63/ |
| Add transaction | http://44.197.147.63/add_transaction |
| Upload receipt | http://44.197.147.63/upload_receipt |
| Insights | http://44.197.147.63/insights |
| Demo reset | http://44.197.147.63/demo_reset |

Screenshots: not captured in this ACI (HTTP/script evidence only).

---

## Blockers

| ID | Issue | Resolution | Status |
|----|-------|------------|--------|
| B1 | Public IP changed after stop/start | Use current IP or `terraform output` after start | **Resolved** — recorded above |
| B2 | Stale `:latest` on instance (pre-hardening) | Pulled pinned tag + systemd restart | **Resolved** |
| B3 | `gina.pem` invalid SSH format (single-line PEM) | Reformatted PEM locally for SSH session only; temp file deleted | **Resolved** |
| B4 | PAPE | Out of scope | **Open** |

---

## Success Criteria Checklist

- [x] SPE-01 started
- [x] Public IP recorded
- [x] Application reachable
- [x] Dashboard validated
- [x] Transactions validated
- [x] Receipt upload validated
- [x] AI insights validated
- [x] Demo Reset validated
- [x] Evidence captured
- [x] Report created

---

## Release Assessment

| Question | Answer |
|----------|--------|
| Is IOR operational in PE? | **Yes**, with pinned image `89a4ea5…` |
| Does PE match deployable artifact? | **Yes**, after on-instance image update |
| Ready for ACI-PE-02? | **Yes** — extended PE / regression / documentation of IP and image pinning |

---

## Recommendation for ACI-PE-02

1. **Document operational runbook:** start instance → confirm public IP → pull pinned SHA (not stale local `latest`) → restart `financial-app`.
2. **Re-run validation** after any future `deployable` push using explicit tag `:${{ github.sha }}`.
3. Consider **ACI-SECURITY-01** before PAPE (HTTP-only, secrets on EBS, SSH exposure).
4. Update operator notes: `terraform output app_url` may differ from historical reports after stop/start.
5. Optional follow-up (future ACI, not PE-01): Terraform/user-data default to pinned tag — out of scope here.

---

## Scope Compliance

- [x] Validation only
- [x] No new AWS resources
- [x] No Terraform code changes or `terraform apply`
- [x] PAPE not declared
- [x] Instance not destroyed (left **running** for follow-on ACIs)
