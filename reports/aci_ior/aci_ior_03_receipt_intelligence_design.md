# ACI-IOR-03 — Receipt Intelligence Design

**Project:** Financial App  
**Date:** 2026-06-04  
**Scope:** Design only — no application code changes  
**Baseline:** `deployable` (post ACI-PA-05 hygiene)

---

## Executive Summary

Receipt Intelligence extends the existing OpenAI vision pipeline from **one flat transaction per receipt** to a **structured workflow** with line items, taxonomy-based categorization, confidence-gated review, and dashboard category summaries. The codebase already requests `items[]` in the model prompt but **drops them** in `parse_receipt_image()`—IOR-04 should close that gap via a new orchestration service and extended transaction schema (**parent transaction + embedded line items**).

---

## 1. Proposed Workflow

```
Upload → Vision parse (header + items[])
  → Normalize + categorize (taxonomy)
  → Confidence gate
       → high: auto-save transaction
       → low/medium: review screen → confirm
  → Dashboard (summaries + breakdown)
  → Insights (category-enriched prompt)
```

---

## 2. Receipt Data Model (header)

**Extract:** merchant, date, subtotal, tax, tip, total, payment_method, currency, confidence, raw_summary, source_image, receipt_id, parse_status.

**Validate:** total ≥ 0; optional sum(items) ≈ total (±$0.05).

---

## 3. Line Item Data Model

**Per line:** line_id, receipt_id, name, quantity, unit_price, line_total, category, category_confidence, optional is_discount.

**Fallback:** single synthetic line when model returns no items.

---

## 4. Category Model

**MVP slugs:** groceries, dining, gas, entertainment, utilities, healthcare, shopping, transport, subscriptions, other, uncategorized.

**Assignment:** model per line → alias map → receipt-level category = weighted mode of line categories.

---

## 5. Transaction Creation Strategy

**Selected:** **One parent transaction per receipt** with embedded `line_items[]` and `receipt_meta` (subtotal/tax/confidence).

**Not selected:** one transaction per line item (dashboard/insights noise).

**Confidence:** high → auto-create; low/medium → `/receipt_review/<id>` before commit.

---

## 6. Architecture Changes

| Layer | Impact |
|-------|--------|
| **Routes** | Modify `/upload_receipt`; add `/receipt_review/<id>`; enrich `/dashboard` |
| **Templates** | New `receipt_review.html`; dashboard summaries |
| **Services** | New `receipt_intelligence_service.py`; extend `openai_receipt_service.py` |
| **Storage** | Optional `receipts.json`; extend `transactions.json` shape (backward compatible) |
| **Utils** | New `receipt_normalize.py`; config `receipt_intelligence.*` |
| **Tests** | New normalize/service/route tests; extend receipt parsing tests |

**Unchanged:** CSRF, auth scope (none), CSV upload, manual add_transaction, demo reset pattern (extend for new files).

---

## 7. Estimated Implementation Complexity

| Rating | **Medium (M)** |
|--------|----------------|
| Phases | 5 (data, service, UI, insights, hardening) |
| Effort | ~3–5 days MVP |
| Risk | Low–medium (schema + UI); mitigated by parent-tx compatibility |

---

## 8. Dashboard Totals (design)

- **Spend total:** sum transaction amounts  
- **Category totals:** group by parent category; optional line-level rollup  
- **Receipt metrics:** count `source=receipt`; link to breakdown  

---

## 9. Design Artifacts

| Artifact | Path |
|----------|------|
| Full specification | `docs/receipt_intelligence/receipt_intelligence_design.md` |
| This report | `reports/aci_ior/aci_ior_03_receipt_intelligence_design.md` |

---

## 10. Recommendation for ACI-IOR-04

1. Branch `feature/receipt-intelligence` from clean `deployable`.  
2. Implement **Phase A → B** first (normalize + service + tests, no UI) to lock schema.  
3. Implement review route + dashboard in **Phase C**.  
4. Run `pytest -v`; update `pe01_validate.py` for high-confidence auto path.  
5. Merge via PA workflow; pin Docker SHA before PE-06.  
6. Do **not** expand auth/TLS scope in IOR-04.

---

## 11. Success Criteria (ACI-IOR-03)

| Criterion | Status |
|-----------|--------|
| Workflow designed | Pass |
| Data model designed | Pass |
| Categories defined | Pass |
| Transaction strategy selected | Pass |
| Architecture impact identified | Pass |
| Implementation plan created | Pass |
| Design doc created | Pass |
| Report created | Pass |

---

## Scope Compliance

- [x] Design only — no code, Terraform, or PE changes
- [x] Ready for ACI-IOR-04 implementation
