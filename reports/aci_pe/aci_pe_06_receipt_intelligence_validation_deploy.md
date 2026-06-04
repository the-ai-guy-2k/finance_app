# ACI-PE-06 — Receipt Intelligence Validation Deployment

**Project:** Financial App  
**Date:** 2026-06-04  
**Scope:** Validation deployment to SPE-01 only (not `deployable` merge, not PAPE)  
**Feature branch:** `feature/receipt-intelligence`  
**Feature commit:** `32a8d2ddfc9b4453d3ef6c4d1895b4243360b14e`

---

## Executive Summary

Receipt Intelligence was deployed to SPE-01 **i-0055c22499e9b2853** by building the Docker image **on the EC2 host** from the public Git branch and restarting `financial-app.service`. The app is reachable at **http://44.192.97.51** with Receipt Intelligence UI and routes confirmed. **Docker Hub publish from CI did not run** (workflow is `deployable`-only; local Docker daemon unavailable).

---

## 1. Branch / Commit Verified

| Item | Value |
|------|--------|
| Branch | `feature/receipt-intelligence` |
| Commit | `32a8d2ddfc9b4453d3ef6c4d1895b4243360b14e` |
| Message | ACI-IOR-04: implement receipt intelligence workflow |
| Cloned on SPE-01 | Same SHA verified after `git clone` |

---

## 2. Docker Image

### Build method (validation deploy)

| Step | Result |
|------|--------|
| GitHub `Docker Publish` on feature branch | **Not triggered** (workflow: `deployable` push + `workflow_dispatch` only) |
| Local `docker build` | **Failed** — Docker Desktop engine not running |
| **SPE-01 on-host build** | **Success** |

### Image identity

| Field | Value |
|-------|--------|
| **Image tag** | `taig2k/finance_app_for_aws:32a8d2ddfc9b4453d3ef6c4d1895b4243360b14e` |
| **Image ID (host)** | `sha256:b7e740eb8a72c1b380391458a96c76365cc74adfdc8e9cc731bc08a120efcd8d` |
| **Docker Hub publish** | **Not performed** — image exists on SPE-01 host only |
| **Prior PE image** | `taig2k/finance_app_for_aws:5175aa9f31ef9889b06df2043215b7c0837e08ba` |

To publish to Hub for reproducibility: run `Docker Publish` workflow via `workflow_dispatch` on `feature/receipt-intelligence` (requires `gh auth` / `GH_TOKEN`) or push from a machine with Docker + Hub credentials.

---

## 3. SPE-01 Update

| Action | Detail |
|--------|--------|
| Instance | `i-0055c22499e9b2853` |
| Public IP | `44.192.97.51` |
| Deploy method | SSH: clone repo → `docker build` → update `/etc/systemd/system/financial-app.service` → `systemctl restart financial-app.service` |
| Terraform apply | **Not run** (validation-only; avoids instance replacement) |
| Service status | **active** |
| Running container image | `taig2k/finance_app_for_aws:32a8d2ddfc9b4453d3ef6c4d1895b4243360b14e` |

---

## 4. Operator URL

**Use this URL for all Receipt Intelligence testing:**

### http://44.192.97.51

| Page | URL |
|------|-----|
| Dashboard | http://44.192.97.51/ |
| Upload receipt | http://44.192.97.51/upload_receipt |
| Insights | http://44.192.97.51/insights |
| Review (after low-confidence upload) | http://44.192.97.51/receipt_review/&lt;receipt_id&gt; |

---

## 5. Validation Results

| Check | Result |
|-------|--------|
| App reachable (`GET /`) | **PASS** — HTTP 200 |
| Dashboard — Spending Summary | **PASS** |
| `/upload_receipt` — Receipt Intelligence wording | **PASS** |
| `/insights` — Category context block | **PASS** |
| `/receipt_review/<id>` route exists | **PASS** — HTTP 302 when pending not found (route registered) |
| `scripts/pe01_validate.py` | **PASS** — 8/8 |
| Gunicorn / container | **PASS** — service active, new image tag |

---

## 6. Known Issues

| ID | Issue | Severity |
|----|-------|----------|
| K1 | Image not on Docker Hub | **Medium** — rebuild required on new instance; use PA-06 publish or workflow_dispatch |
| K2 | `terraform.tfvars` still pins `5175aa9…` | **Low** — manual deploy used; TF apply would revert until updated |
| K3 | On-host build not in standard CI path | **Info** — acceptable for validation deploy |
| K4 | PAPE not evaluated | **Info** — out of scope |

---

## 7. Operator Test Instructions — Receipt Upload

### A. Confirm Receipt Intelligence UI

1. Open http://44.192.97.51/upload_receipt  
2. Confirm helper text mentions **“Receipt Intelligence”** and **“review screen”**.

### B. High-confidence auto-save (typical clear receipt)

1. Upload a clear photo of a store receipt (PNG/JPG, &lt; 10 MB).  
2. If parsing confidence is **high**, you are redirected to the dashboard with a success flash.  
3. On the dashboard, verify **Spending Summary** and a transaction with **Source: Receipt (N items)**.

### C. Low/medium confidence → review screen

1. Upload a blurry or partial receipt (or fallback parse).  
2. You should be redirected to **/receipt_review/&lt;uuid&gt;** with editable merchant, totals, and line items.  
3. Click **Confirm & Save** → dashboard shows the transaction.  
4. **Discard** removes the pending receipt without saving.

### D. Insights

1. Open http://44.192.97.51/insights  
2. Confirm **Category context** section and narrative insights reference spending/receipts.

### E. Regression smoke

- Add manual transaction: http://44.192.97.51/add_transaction  
- Demo reset still works: http://44.192.97.51/demo_reset  

---

## 8. Success Criteria

| Criterion | Status |
|-----------|--------|
| Feature branch deployed | **Pass** (commit `32a8d2d` on SPE-01) |
| New image published | **Partial** — built on host; Hub publish pending |
| SPE-01 updated | **Pass** |
| App reachable | **Pass** |
| Receipt Intelligence route exists | **Pass** |
| Upload page updated | **Pass** |
| Operator URL provided | **Pass** |
| Report created | **Pass** |

---

## 9. Recommendation for ACI-PA-06

1. Publish `32a8d2d…` to Docker Hub via `workflow_dispatch` on `feature/receipt-intelligence` or merge path per governance.  
2. Optionally update `terraform.tfvars` `docker_image` to the RI tag before any Terraform-driven redeploy.  
3. After operator sign-off, merge `feature/receipt-intelligence` → `deployable` (separate ACI).  
4. Do **not** declare PAPE until auth/TLS and SSM-from-instance gaps from PE-04 are closed.

---

## Scope Compliance

- [x] Validation deployment to SPE-01  
- [x] Operator live URL enabled  
- [x] No `deployable` merge  
- [x] No PAPE declaration  
- [x] No resource destruction
