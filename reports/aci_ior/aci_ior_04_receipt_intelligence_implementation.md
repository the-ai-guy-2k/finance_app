# ACI-IOR-04 — Receipt Intelligence Implementation

**Project:** Financial App  
**Date:** 2026-06-04  
**Branch:** `feature/receipt-intelligence` (not merged to `deployable`)  
**Design authority:** `docs/receipt_intelligence/receipt_intelligence_design.md`

---

## Executive Summary

Receipt Intelligence is implemented per IOR-03: structured vision parse, line items, taxonomy categorization, confidence-gated review, parent transaction with `line_items[]` and `receipt_meta`, dashboard summaries, and enriched insights. **43 pytest tests pass.** Branch ready for PA merge workflow and ACI-PE-06 validation.

---

## 1. Branch

`feature/receipt-intelligence` (from `deployable` post ACI-PA-05)

---

## 2. Files Modified / Added

### New modules

| File | Purpose |
|------|---------|
| `app/utils/receipt_categories.py` | Taxonomy slugs, labels, aliases |
| `app/utils/receipt_normalize.py` | Header/line normalization, confidence gate, parent tx build |
| `app/utils/dashboard_stats.py` | Category/receipt summaries, insights context |
| `app/services/receipt_intelligence_service.py` | Upload orchestration, review confirm |
| `app/templates/receipt_review.html` | Low/medium confidence review UI |

### New tests

| File | Coverage |
|------|----------|
| `tests/test_receipt_normalize.py` | Normalization, mismatch, confidence |
| `tests/test_receipt_intelligence_service.py` | Auto-commit vs review, confirm |
| `tests/test_dashboard_stats.py` | Summaries, backward compatibility |
| `tests/test_receipt_routes.py` | Review route, upload redirect |

### Updated

| File | Change |
|------|--------|
| `app/services/openai_receipt_service.py` | `parse_receipt_structured()`, extended prompt, flat compat |
| `app/services/openai_service.py` | Insights use category/receipt context |
| `app/routes/main.py` | Intelligence flow, `/receipt_review/<id>`, `/uploads/<file>`, dashboard |
| `app/utils/storage.py` | Pending receipts, receipts archive, demo reset |
| `app/templates/dashboard.html` | Summaries, receipt source column |
| `app/templates/upload_receipt.html` | Intelligence copy |
| `app/templates/insights.html` | Category context block |
| `config.docker.example.json` | `receipt_intelligence` config |
| `.gitignore` | `data/receipts.json`, `data/receipts_pending.json` |

---

## 3. New Routes

| Route | Methods | Purpose |
|-------|---------|---------|
| `/receipt_review/<receipt_id>` | GET, POST | Review/confirm/discard pending receipts |
| `/uploads/<filename>` | GET | Serve receipt images for review UI |

`/upload_receipt` POST now uses `ReceiptIntelligenceService` (auto-save or redirect to review).

---

## 4. New Data Structures

### Receipt header

`receipt_id`, `merchant`, `date`, `subtotal`, `tax`, `tip`, `total`, `payment_method`, `currency`, `confidence`, `parse_status`, `source_image`, `raw_summary`

### Line item

`line_id`, `receipt_id`, `name`, `quantity`, `unit_price`, `line_total`, `category`, `category_confidence`, `is_discount`

### Parent transaction (extended)

- `source`: `"receipt"`
- `receipt_id`
- `line_items[]`
- `receipt_meta`: subtotal, tax, tip, payment_method, currency, confidence, parse_status, source_image

### Storage files (runtime, gitignored)

- `data/receipts_pending.json` — review queue
- `data/receipts.json` — confirmed receipt headers archive

---

## 5. Dashboard Changes

- Spending summary: total spend, receipt count, receipt spend
- Category totals list with labels
- Transaction table: **Source** column (receipt + item count)

---

## 6. Insight Changes

- OpenAI prompt includes `category_totals`, `line_category_totals`, `receipt_summaries`, receipt count
- Heuristic fallback reports receipt count and top line-item category
- Insights page shows category context panel

---

## 7. Test Results

```
pytest -v → 43 passed
```

Includes existing suite plus 15 new receipt intelligence tests.

---

## 8. Backward Compatibility

- Legacy transactions without `line_items` / `receipt_meta` load and display normally
- `parse_receipt_image()` still returns flat dict for existing tests
- Manual add/CSV flows unchanged

---

## 9. Blockers

| ID | Blocker | Notes |
|----|---------|-------|
| — | None for implementation | — |
| N1 | Not merged to `deployable` | Per ACI stop point |
| N2 | PE-06 not run | Requires merge + Docker publish + SPE-01 deploy |

---

## 10. Recommendation for ACI-PE-06

1. Merge `feature/receipt-intelligence` → `deployable` via PA workflow.
2. Confirm CI + Docker publish; pin new SHA on SPE-01.
3. Run `scripts/pe01_validate.py` against PE — add receipt review path test if low-confidence sample available.
4. Validate dashboard summaries and insights on live URL.
5. Do not declare PAPE (out of scope).

---

## Success Criteria

| Criterion | Status |
|-----------|--------|
| Receipt breakdown | Pass |
| Line item extraction | Pass |
| Categorization | Pass |
| Auto transaction creation | Pass |
| Review screen | Pass |
| Dashboard updated | Pass |
| Insights updated | Pass |
| Backward compatibility | Pass |
| Tests pass | Pass (43) |
| Report created | Pass |
