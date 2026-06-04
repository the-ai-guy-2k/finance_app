# Receipt Intelligence — Design Specification

**ACI:** ACI-IOR-03  
**Status:** Design only (no implementation)  
**Branch baseline:** `deployable` post ACI-PA-05  
**Date:** 2026-06-04

---

## 1. Purpose

Evolve receipt handling from **single lump-sum transaction extraction** to **structured receipt intelligence**: line-item breakdown, per-item categorization, confidence-aware review, and dashboard-ready aggregates—while preserving existing security (CSRF), storage patterns, and insights pipeline.

---

## 2. Current vs Target Workflow

### Current (as implemented)

```
Receipt Upload → Save image → OpenAI vision (flat JSON)
  → normalize_transaction() → append to transactions.json
  → Dashboard (flat table) → Insights (flat tx list)
```

**Gap:** OpenAI prompt already requests `items[]` and `confidence`, but `OpenAIReceiptParsingService.parse_receipt_image()` **discards** line items and confidence, emitting only merchant/amount/date/category/note.

### Target

```
Receipt Upload
  → Receipt Read (vision + OCR-quality image handling)
  → Line Item Extraction
  → Item Categorization (taxonomy + rules)
  → Confidence Gate
       ├─ high → Automatic Transaction Creation
       └─ low/medium → Review Screen → User confirm/edit
  → Persist Receipt + Line Items + Parent Transaction
  → Dashboard Update (receipt + category summaries)
  → Insight Generation (enriched context: items + categories)
```

---

## 3. Receipt Header Data Model

### 3.1 Fields to extract

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `merchant` | string | yes | Store name; fallback to filename |
| `date` | ISO date string | no | Receipt date; default empty → normalize uses UTC now |
| `subtotal` | decimal string | no | Pre-tax subtotal when visible |
| `tax` | decimal string | no | Sales tax/VAT |
| `tip` | decimal string | no | Gratuity when present |
| `total` | decimal string | yes | Primary amount; maps to transaction `amount` |
| `payment_method` | enum string | no | `cash`, `credit`, `debit`, `unknown` |
| `currency` | string | no | Default `USD` for MVP |
| `receipt_id` | UUID | yes | Internal ID linking storage artifacts |
| `source_image` | string | yes | Relative path under `uploads/` |
| `confidence` | enum | yes | `high`, `medium`, `low` (receipt-level) |
| `raw_summary` | string | no | Model narrative for notes/audit |
| `parse_status` | enum | yes | `parsed`, `fallback`, `review_pending`, `confirmed` |

### 3.2 Validation rules

- `total` must parse as float ≥ 0; if line items present, `sum(line_items.line_total)` should equal `total` within **±$0.05** tolerance (flag mismatch → lower confidence).
- If `subtotal` + `tax` + `tip` visible, validate against `total` within tolerance.
- Unknown fields → empty string or `null`; never block save on optional fields.

### 3.3 Storage (proposed)

New file: `data/receipts.json` (array of receipt header objects), **or** embed `receipt` object on parent transaction (see §6). Recommendation: **separate `receipts.json`** for audit/re-parse without bloating transaction rows.

---

## 4. Line Item Data Model

### 4.1 Fields per line item

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `line_id` | UUID | yes | Unique within receipt |
| `receipt_id` | UUID | yes | FK to receipt header |
| `name` | string | yes | Item description |
| `quantity` | number | no | Default `1` |
| `unit_price` | decimal string | no | Per-unit when visible |
| `line_total` | decimal string | yes | Extended price |
| `category` | string | yes | From taxonomy (§5) |
| `category_confidence` | enum | yes | `high`, `medium`, `low` |
| `sku` | string | no | Future; optional |
| `is_discount` | boolean | no | Negative lines / coupons |

### 4.2 Extraction strategy

1. **Primary:** OpenAI vision returns `items[]` in structured JSON (extend existing prompt; increase `max_tokens` to ~1200).
2. **Normalization layer:** `app/utils/receipt_normalize.py` (new) coerces types, assigns categories via map + model category.
3. **Fallback:** If `items` empty but `total` present → single synthetic line item `"Receipt total"` with full amount.

---

## 5. Category Model

### 5.1 Canonical taxonomy (MVP)

| Slug | Display label | Examples |
|------|---------------|----------|
| `groceries` | Groceries | supermarket, produce |
| `dining` | Dining | restaurant, café, fast food |
| `gas` | Gas / Fuel | station, fuel line |
| `entertainment` | Entertainment | movies, games |
| `utilities` | Utilities | electric, water on bill |
| `healthcare` | Healthcare | pharmacy, clinic |
| `shopping` | Shopping | retail, clothing |
| `transport` | Transport | parking, transit |
| `subscriptions` | Subscriptions | streaming, SaaS on receipt |
| `other` | Other | unclassified |
| `uncategorized` | Uncategorized | parse failure only |

### 5.2 Assignment rules

1. Model proposes category per line (and receipt-level default).
2. **Alias map** in `config.json` or `data/category_aliases.json` (e.g. `food` → `dining`, `fuel` → `gas`).
3. Receipt-level category = **mode** of line categories by `line_total` weight; ties → `other`.
4. Dashboard badges use slug; human-readable label in templates.

### 5.3 Future (out of IOR-03 scope)

- User-defined categories
- Learning from user corrections on review screen

---

## 6. Confidence Handling

### 6.1 Signals

| Signal | Effect |
|--------|--------|
| Model `confidence: high` + JSON valid + total matches items | **Auto-create** |
| Model `medium` OR total mismatch ≤ $1 | **Review recommended** |
| Model `low` OR fallback parse OR empty merchant | **Review required** |
| Any line `category_confidence: low` | **Review required** (even if receipt high) |

### 6.2 Thresholds (configurable)

```json
"receipt_intelligence": {
  "auto_create_min_confidence": "high",
  "review_required_confidence": ["low", "medium"],
  "amount_mismatch_tolerance": 0.05
}
```

### 6.3 Review screen (new route)

- **Route:** `GET/POST /receipt_review/<receipt_id>`
- Shows: image thumbnail, header fields (editable), line item table (editable category/amount).
- Actions: **Confirm** → persist transaction + mark `parse_status: confirmed`; **Discard** → delete pending receipt artifact.
- CSRF on POST (existing pattern).

---

## 7. Transaction Creation Strategy

### 7.1 Selected approach: **Parent transaction + line item detail**

**Rationale:**

- Dashboard and insights already consume `transactions.json`; one **parent** row per receipt preserves backward compatibility.
- Line items enable breakdown, category totals, and richer insights without N separate dashboard rows per receipt (avoid clutter).
- CSV/manual entries remain flat transactions without `receipt_id`.

### 7.2 Parent transaction shape (extended)

```json
{
  "id": "uuid",
  "merchant": "Costco",
  "amount": "87.42",
  "date": "2026-06-01",
  "category": "groceries",
  "note": "Receipt: 3 items | Tax $5.42",
  "source": "receipt",
  "receipt_id": "uuid",
  "line_items": [
    {
      "line_id": "uuid",
      "name": "Organic milk",
      "quantity": 1,
      "line_total": "4.99",
      "category": "groceries",
      "category_confidence": "high"
    }
  ],
  "receipt_meta": {
    "subtotal": "82.00",
    "tax": "5.42",
    "payment_method": "credit",
    "confidence": "high",
    "parse_status": "confirmed"
  }
}
```

### 7.3 Alternatives considered

| Strategy | Pros | Cons | Decision |
|----------|------|------|----------|
| One tx per receipt only (current) | Simple | No breakdown | **Reject** for target |
| One tx per line item | Granular sums | Dashboard noise; breaks insights count | **Reject** for MVP |
| Parent + line items | Compatible + rich | Slightly larger JSON | **Adopt** |

### 7.4 Auto-create vs review

- **High confidence:** POST upload → parse → normalize → save parent+items → flash success → dashboard.
- **Low/medium:** POST upload → parse → save **pending** receipt to session or `data/receipts_pending.json` → redirect review → on confirm, write transaction.

---

## 8. Dashboard & Totals

### 8.1 Transaction table (existing)

- Unchanged columns for flat/manual txs.
- Receipt-sourced rows: optional **expand** row or link “View breakdown” → receipt detail partial.

### 8.2 New summary blocks (dashboard)

| Block | Calculation |
|-------|-------------|
| **Period spend** | Sum `amount` for txs in optional date filter (MVP: all time) |
| **By category** | Sum parent `amount` grouped by `category`; optional secondary sum of `line_items[].line_total` by line category |
| **Receipt count** | Count txs where `source == 'receipt'` |
| **Last receipt** | Most recent by `date` with link to breakdown |

### 8.3 Insights enrichment

- Pass to `OpenAIService.generate_insights()`:
  - Flat transactions (as today)
  - Plus compact `category_totals` and top merchants from line items
- Heuristic fallback already aggregates by category; extend to use line-level weights when present.

---

## 9. Architecture Impact

### 9.1 Routes (`app/routes/main.py` or new `receipt_routes.py`)

| Route | Change |
|-------|--------|
| `/upload_receipt` | POST branches on confidence; may redirect to review |
| `/receipt_review/<id>` | **New** GET/POST |
| `/receipt/<id>` | **New** GET detail (optional MVP) |
| `/dashboard` | Pass category summaries |
| `/insights` | No route change; richer payload to service |

### 9.2 Templates

| Template | Change |
|----------|--------|
| `upload_receipt.html` | Copy: line items + review hint |
| `receipt_review.html` | **New** |
| `dashboard.html` | Category summary + expandable receipt rows |
| `insights.html` | Optional “based on N receipts with line detail” |
| `base.html` | Nav link to upload unchanged |

### 9.3 Services

| Module | Change |
|--------|--------|
| `openai_receipt_service.py` | Return full structured payload; separate map-to-domain step |
| `receipt_intelligence_service.py` | **New** orchestration: extract → categorize → confidence → build tx |
| `openai_service.py` | Insights prompt includes line/category aggregates |
| `openai_service.parse_receipt` | Deprecate/stub (already legacy) |

### 9.4 Utils / storage

| Module | Change |
|--------|--------|
| `normalize.py` | Extend or add `normalize_receipt_transaction()` |
| `receipt_normalize.py` | **New** line items + taxonomy |
| `storage.py` | `load/save_receipts()`, pending receipts; optional helpers |
| `config_manager` | `receipt_intelligence.*` config block |

### 9.5 Tests

| Area | Tests |
|------|-------|
| `test_receipt_normalize.py` | **New** — taxonomy, tolerance, synthetic line |
| `test_receipt_intelligence_service.py` | **New** — confidence gates (mocked OpenAI) |
| `test_openai_receipt_parsing.py` | Extend for `items[]` preservation |
| `test_routes_receipt_review.py` | **New** — CSRF, confirm flow |
| `scripts/pe01_validate.py` | Optional receipt review smoke (IOR-04/PE-06) |

### 9.6 Config & docs

- `config.json` / `config.docker.example.json`: `receipt_intelligence` section
- Update `docs/PCAP_openai_receipt_parsing.md` or cross-link to this doc

### 9.7 Non-goals (this feature)

- Authentication / authorization
- HTTPS termination
- Multi-user accounts
- Persistent ML training pipeline

---

## 10. OpenAI Prompt Evolution (design)

Extend JSON schema returned by vision model:

```json
{
  "merchant": "",
  "date": "",
  "subtotal": 0.0,
  "tax": 0.0,
  "tip": 0.0,
  "total": 0.0,
  "payment_method": "",
  "currency": "USD",
  "category": "",
  "confidence": "high",
  "raw_summary": "",
  "items": [
    {
      "name": "",
      "quantity": 1,
      "unit_price": 0.0,
      "line_total": 0.0,
      "category": "",
      "category_confidence": "high"
    }
  ]
}
```

Post-processing in Python—not additional model calls for MVP categorization (single call keeps cost/latency predictable).

---

## 11. Implementation Plan (ACI-IOR-04)

### Phase A — Data layer (S)
1. `receipt_normalize.py` + taxonomy constants  
2. Extend transaction schema with optional `line_items`, `receipt_meta`, `source`  
3. Storage helpers + migration note for existing `transactions.json` (backward compatible reads)

### Phase B — Service layer (M)
1. `ReceiptIntelligenceService` wrapping `OpenAIReceiptParsingService`  
2. Confidence gate + pending receipt store  
3. Unit tests with fixtures (sample JSON, no live API)

### Phase C — UI & routes (M)
1. Review template + routes  
2. Upload flow branch  
3. Dashboard summaries + breakdown UI

### Phase D — Insights & validation (S)
1. Insights prompt enrichment  
2. Extend pytest + `pe01_validate.py`  
3. Update PCAP / LOCAL_TESTING

### Phase E — Hardening (S)
1. Amount mismatch warnings in review UI  
2. Demo reset clears `receipts.json` / pending  
3. Error logging categories

**Estimated total complexity:** **Medium (M)** — ~3–5 dev days for careful MVP; low risk to security posture if CSRF/tests preserved.

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Model invents line items | Confidence + review; show raw_summary |
| Token/latency increase | Cap items at 50; truncate in prompt |
| JSON schema drift | Strict parser + fallback single-line |
| Dashboard breaking | Parent tx still has `amount`; old txs without `line_items` OK |
| Demo reset incomplete | Extend `reset_demo_data()` for new files |

---

## 13. Success Criteria Mapping (ACI-IOR-03)

| Criterion | Section |
|-----------|---------|
| Workflow designed | §2 |
| Data model designed | §3–4 |
| Categories defined | §5 |
| Transaction strategy selected | §7 |
| Architecture impact identified | §9 |
| Implementation plan created | §11 |
| Design doc created | This file |

---

## 14. References

- `app/services/openai_receipt_service.py` — current parser (prompt includes `items[]`, output flattened)
- `app/routes/main.py` — `/upload_receipt`, `/insights`
- `app/utils/normalize.py` — transaction normalization
- `docs/PCAP_openai_receipt_parsing.md` — prior PCAP
