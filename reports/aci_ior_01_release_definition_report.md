# ACI-IOR-01 Release Definition Report

**Report ID:** ACI-IOR-01  
**Timestamp:** 2026-06-03  
**Branch:** `feature/ior-release-definition`  
**Mission:** Define Initial Official Release (IOR) for Financial App

---

## Executive Summary

IOR v1 is **defined** in `docs/nebula/ior/financial_app_ior_v1.md`. The current application already delivers most core demo capabilities; **demo reset** and **deployed AI insights validation** are the primary gaps before IOR/PAPE sign-off.

**Final recommendation:** Proceed to feature ACIs for P0 items, then PE validation — **do not merge** this branch to `deployable` until DWN review (per stop point).

---

## Application Review Summary

### Routes reviewed

| Route | Function |
|-------|----------|
| `/` | Dashboard |
| `/upload_receipt` | Receipt upload + AI parse |
| `/upload_csv` | CSV ingest |
| `/add_transaction` | Manual entry |
| `/insights` | AI insight generation |

### Templates

`base.html`, `dashboard.html`, `upload_receipt.html`, `upload_csv.html`, `add_transaction.html`, `insights.html`, `error.html`

### Services / storage

- `OpenAIReceiptParsingService` — vision receipt parsing (modern OpenAI SDK)
- `OpenAIService` — insights (legacy ChatCompletion API path)
- `storage.py` — `transactions.json`; goals hardcoded in `get_default_goals()`
- `normalize.py` — transaction schema normalization

---

## 1. Existing Feature Summary

| Feature | Status |
|---------|--------|
| Dashboard with transaction table | **Implemented** |
| Navigation (5 screens) | **Implemented** |
| Manual transaction entry | **Implemented** |
| CSV upload | **Implemented** |
| Receipt upload (format/size validation) | **Implemented** |
| OpenAI receipt parsing (vision + JSON) | **Implemented** |
| AI insights page | **Implemented** (heuristic fallback if OpenAI fails) |
| Goals display | **Partial** — single hardcoded goal |
| Transaction normalization | **Implemented** |
| Local JSON persistence | **Implemented** |
| Preflight validation | **Implemented** |
| Flash messages / error page | **Implemented** |
| CSS professional theme | **Implemented** |
| Docker / CI / deployable branch | **Implemented** |
| SPE-01 hosting path | **Proven** (PE created, stopped) |

---

## 2. Missing Feature Summary (for IOR v1)

| Feature | Priority | Notes |
|---------|----------|-------|
| **Demo reset** | **P0** | No route or storage clear — required for IOR |
| **AI insights validation on deployable** | **P0** | Code exists; PE must confirm non-heuristic output in container |
| Receipt service `OPENAI_API_KEY` env support | P1 | SPE-01 uses env; receipt parser reads file path only |
| Transaction edit/delete | Deferred | Demo reset substitutes for v1 |
| User-defined goals (`goals.json`) | Deferred | Static display sufficient for v1 |
| Authentication | Not IOR | — |

---

## 3. IOR Spec Path

[`docs/nebula/ior/financial_app_ior_v1.md`](../docs/nebula/ior/financial_app_ior_v1.md)

---

## 4. Report Path

`reports/aci_ior_01_release_definition_report.md` (this file)

---

## 5. Branch Name

**`feature/ior-release-definition`**

---

## 6. Recommended Next ACI-IOR Sequence

| Order | ACI (suggested) | Purpose |
|-------|-----------------|---------|
| 1 | **ACI-IOR-02** | Implement demo reset (route + clear `transactions.json` / uploads) |
| 2 | **ACI-IOR-03** | Align OpenAI key loading (env var) for receipt + insights services |
| 3 | **ACI-IOR-04** | Fix/validate insights OpenAI SDK v1 compatibility on `deployable` |
| 4 | **ACI-IOR-05** | Resume SPE-01 PE validation (`VALIDATION.md`) with IOR checklist |
| 5 | **ACI-IOR-06** | PAPE decision / release sign-off documentation |

Feature branches merge to `deployable` only after CI passes.

---

## 7. Blockers

**None** for IOR definition work.

**Before PAPE:**

- P0 features (demo reset, AI validation on deploy)
- Full PE validation not completed (PAPE explicitly not declared)

---

## 8. Final Recommendation

**IOR definition: COMPLETE**

Use `financial_app_ior_v1.md` as the authoritative scope document for all subsequent IOR feature ACIs. Do not implement out-of-scope items (bank integrations, multi-user, mobile, etc.) until a future release.

**Can proceed to ACI-IOR-02:** **Yes** (demo reset implementation).

---

## Scope Compliance

- No application code modified (planning docs only)
- No Terraform / AWS actions
- Branch pushed; **not** merged to `deployable`
