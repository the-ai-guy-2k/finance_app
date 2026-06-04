# Receipt Intelligence v2 — Behavioral Design Specification

**ACI:** ACI-IOR-05  
**Status:** Design only (no implementation)  
**Branch baseline:** `feature/receipt-intelligence-v2` / `deployable` post ACI-PA-06  
**Date:** 2026-06-04  
**Design authority:** `Financial_App_Receipt_Intelligence_Restoration_Export` (conceptual mapping §2)

---

## 1. Mission Shift: v1 → v2

| Version | Question answered |
|---------|-------------------|
| **v1** | *What was purchased?* — extraction, line items, taxonomy, confidence, parent transaction |
| **v2** | *Why was it purchased? What does it mean? What behavior does it represent?* — behavioral intelligence layer |

v2 **extends** v1; it does not replace extraction, review, or storage patterns from `receipt_intelligence_design.md`.

---

## 2. Restoration Export Provenance

**Primary source (named authority):** `Financial_App_Receipt_Intelligence_Restoration_Export`

The restoration export was **not present** in the Financial App repository at design time. This document **extracts and organizes** the highest-value behavioral concepts from:

1. Restoration export **section intent** as specified in ACI-IOR-05 (seven design areas + behavioral summary).
2. Implemented v1 artifacts (`line_items[]`, `receipt_meta`, merchant/category history).
3. Financial App philosophy: *behavioral problems, not mathematical* (`aci.md`).

When the export file is added to `docs/receipt_intelligence/`, map each §3–§9 block to export section IDs and reconcile enums verbatim.

### Export concept map (RIE)

| RIE ID | Export concept | Design section |
|--------|----------------|----------------|
| RIE-E01 | Essential / non-essential classification | §4 |
| RIE-T01 | Trip / basket intent | §5 |
| RIE-B01 | Behavioral tags | §6 |
| RIE-S01 | Savings & waste signals | §7 |
| RIE-M01 | Merchant intelligence | §8 |
| RIE-H01 | Habit & repeat detection | §9 |
| RIE-SUM01 | Behavioral receipt summary | §10 |

---

## 3. Behavioral Intelligence Architecture

### 3.1 Pipeline (post–v1 confirm)

```
v1: Upload → Parse → Categorize → Confidence → Transaction saved
                    ↓
v2: Load receipt + line_items + user history (90-day window)
    → Rules engine (essential, trip, tags, habits, savings heuristics)
    → Optional OpenAI enrichment (structured JSON only)
    → Merge scores + confidence
    → Attach behavioral_meta to transaction
    → Dashboard behavioral panel + insights payload
    → Persist behavioral summary on receipt archive
```

### 3.2 Design principles (from restoration intent)

- **Rules-first, AI-enhanced** — same as app-wide architecture; AI explains and refines, does not sole-source classifications.
- **Explainability** — every classification exposes `reason_codes[]` (short machine keys + optional user string).
- **Confidence everywhere** — no silent high-stakes labels at low confidence; surface review hints when behavioral confidence is low.
- **Backward compatible** — transactions without `behavioral_meta` render as v1-only.

### 3.3 New service (implementation target for IOR-06)

| Module | Role |
|--------|------|
| `BehavioralReceiptIntelligenceService` | Orchestrate v2 after v1 commit |
| `behavioral_rules.py` | Deterministic trip/essential/tag/habit/savings rules |
| `behavioral_normalize.py` | Coerce model output, clamp scores, validate enums |
| `merchant_memory.py` | Rolling merchant stats from `transactions.json` |

---

## 4. Essential vs Non-Essential Model (RIE-E01)

### 4.1 Classification enum

| Value | Meaning |
|-------|---------|
| `essential` | Required for health, safety, housing, core nutrition, prescribed care |
| `non_essential` | Discretionary / lifestyle without necessity |
| `discretionary` | Optional but reasonable (e.g. modest dining out) |
| `mixed` | Basket splits essential and non-essential materially |
| `unknown` | Insufficient signal |

### 4.2 Scoring method

| Field | Type | Range | Notes |
|-------|------|-------|-------|
| `essential_score` | float | 0.0–1.0 | 1.0 = fully essential |
| `non_essential_score` | float | 0.0–1.0 | Complement normalized: `essential + non_essential ≈ 1` |
| `classification` | enum | §4.1 | Derived from scores + thresholds |

**Line-level first, receipt-level aggregate:**

1. Score each `line_item` using category priors + keyword lexicon (e.g. “medicine”, “rent”, “fuel” vs “candy”, “toy”).
2. Receipt `essential_score` = **amount-weighted mean** of line scores.
3. If spread > 0.4 between min/max line scores → `classification = mixed`.

### 4.3 Thresholds (configurable)

```json
"behavioral_intelligence": {
  "essential_threshold_high": 0.75,
  "essential_threshold_low": 0.35,
  "mixed_spread_threshold": 0.40
}
```

- `essential_score >= 0.75` → `essential`
- `essential_score <= 0.35` → `non_essential`
- Between → `discretionary` unless mixed spread triggers `mixed`

### 4.4 Confidence method

| Signal | Effect |
|--------|--------|
| All lines `category_confidence: high` | +0.2 behavioral confidence |
| Merchant prior ≥ 5 receipts | +0.15 |
| Keyword hit on ≥ 60% of spend | +0.1 |
| Fallback / sparse lines | cap confidence at `low` |

Output: `essential_confidence`: `high` | `medium` | `low`

### 4.5 Storage shape

```json
"essential": {
  "classification": "mixed",
  "essential_score": 0.58,
  "non_essential_score": 0.42,
  "confidence": "medium",
  "line_scores": [{"line_id": "…", "score": 0.9, "classification": "essential"}],
  "reason_codes": ["MIXED_BASKET", "GROCERY_BASE"]
}
```

---

## 5. Trip Classification Model (RIE-T01)

### 5.1 Trip type taxonomy

| `trip_type` | Definition | Typical signals |
|-------------|------------|-----------------|
| `grocery_restock` | Planned food/household stock-up | Supermarket merchant, ≥5 grocery lines, high subtotal |
| `convenience_run` | Small, time-sensitive top-up | C-store merchant, ≤5 lines, premium pricing |
| `refill_trip` | Repeat consumable replenishment | High overlap with prior receipt lines (§9) |
| `impulse_purchase` | Unplanned discretionary buy | Single non-essential line or snack aisle pattern |
| `maintenance_purchase` | Upkeep (auto, home, tools) | Category utilities/transport + maintenance keywords |
| `emergency_purchase` | Urgent necessity | Pharmacy + health, late hour, “urgent” keywords |
| `mixed_basket` | Multiple intents in one trip | ≥2 trip signals within 0.3 score of top |
| `unknown` | No dominant signal | Default |

### 5.2 Classification logic (rules-first)

**Score each trip_type 0–1; winner = max score if lead ≥ 0.45, else `mixed_basket` if second within 0.15, else `unknown`.**

| Rule ID | Condition | Boost trip_type |
|---------|-----------|-----------------|
| T-R01 | Merchant in `grocery_merchants` list | `grocery_restock` +0.35 |
| T-R02 | Line count ≤ 4 AND total < $25 | `convenience_run` +0.3 |
| T-R03 | ≥70% line names match prior receipt (30d) | `refill_trip` +0.4 |
| T-R04 | Single line AND non_essential_score > 0.7 | `impulse_purchase` +0.35 |
| T-R05 | maintenance category dominance | `maintenance_purchase` +0.35 |
| T-R06 | health category + emergency keywords | `emergency_purchase` +0.4 |
| T-R07 | Top two trip scores both > 0.35 | `mixed_basket` |

**AI assist:** Optional prompt returns `trip_type` + `trip_scores{}` + rationale; rules override if AI confidence low.

### 5.3 Confidence

`trip_confidence` from rule margin (top − second score) and merchant prior depth.

---

## 6. Behavioral Tag Model (RIE-B01)

### 6.1 Tag vocabulary

| Tag | Meaning |
|-----|---------|
| `convenience` | Paying for proximity/time (small basket, C-store, delivery fee lines) |
| `impulse` | Unplanned discretionary item |
| `recurring` | Matches known recurring item/merchant cadence |
| `luxury` | Premium/discretionary non-necessity |
| `maintenance` | Upkeep/repair/consumable replacement |
| `social` | Dining/entertainment with social context keywords |
| `health` | Health-related necessity |
| `productivity` | Work/tools/education supporting income |

Tags are **multi-select** with per-tag strength 0–1.

### 6.2 Assignment

1. **Keyword + category triggers** per tag (lexicon in config).
2. **Cross-signal boosts** (e.g. `convenience_run` → `convenience` +0.3).
3. **Model proposes** supplemental tags; include only if `strength >= 0.5` and `confidence >= medium`.

### 6.3 Output

```json
"behavioral_tags": [
  {"tag": "convenience", "strength": 0.72, "confidence": "high", "reason": "SMALL_BASKET_CSTORE"},
  {"tag": "recurring", "strength": 0.55, "confidence": "medium", "reason": "LINE_MATCH_PRIOR"}
]
```

---

## 7. Savings Opportunity Model (RIE-S01)

### 7.1 Detection methods

| Opportunity | Detection | Output field |
|-------------|-----------|--------------|
| **Convenience cost** | Compare unit price vs category median OR basket size vs merchant type | `convenience_premium_estimate` (USD) |
| **Recurring spend awareness** | Cadence ≤ 30d same merchant+line | `recurring_spend_alert` (bool + annualized_estimate) |
| **Avoidable spend** | Non-essential lines with impulse tag strength > 0.6 | `avoidable_spend_total` |
| **Category concentration** | User spends >40% of 30d spend in one category | `concentration_warning` (category + pct) |

### 7.2 Scoring

`savings_opportunity_score` 0–1 = normalized sum of flagged opportunities (capped).

Only surface opportunities with `confidence >= medium` in UI.

### 7.3 Output

```json
"savings": {
  "opportunity_score": 0.61,
  "convenience_premium_estimate": "3.50",
  "avoidable_spend_total": "12.99",
  "recurring_spend_alert": true,
  "recurring_annualized_estimate": "156.00",
  "concentration_warning": {"category": "dining", "pct_30d": 0.43},
  "suggestions": [
    "Consolidate convenience runs into weekly grocery restock",
    "Recurring subscription line detected — review necessity"
  ],
  "confidence": "medium"
}
```

---

## 8. Merchant Intelligence Model (RIE-M01)

### 8.1 Merchant profile (rolling)

Per merchant slug (normalized name):

| Field | Description |
|-------|-------------|
| `visit_count_30d` | Frequency |
| `avg_basket` | Mean receipt total |
| `dominant_trip_type` | Mode of trip_type |
| `essential_bias` | Mean essential_score |
| `top_categories` | Weighted categories |

### 8.2 Merchant behavior scoring

`merchant_behavior_score` 0–1:

- High frequency + rising avg basket → spend acceleration signal
- High non_essential_bias → discretionary merchant flag
- Stable refill pattern → low risk

### 8.3 Receipt-level merchant block

```json
"merchant_intelligence": {
  "merchant_key": "costco_wholesale",
  "visit_count_30d": 3,
  "avg_basket": "87.42",
  "essential_bias": 0.71,
  "dominant_trip_type": "grocery_restock",
  "behavior_score": 0.42,
  "pattern_label": "stable_restock",
  "confidence": "high"
}
```

---

## 9. Habit Detection Model (RIE-H01)

### 9.1 Detectors

| Detector | Logic | Output |
|----------|-------|--------|
| **Repeat purchases** | Line name fuzzy match (≥0.85) across receipts 30–90d | `repeat_items[]` |
| **Repeat merchants** | Same `merchant_key` with cadence 7±2 or 30±3 days | `merchant_cadence` |
| **Repeat categories** | Category ≥25% of rolling spend | `category_habit` |
| **Spending patterns** | Day-of-week / time-of-day mode (if timestamp available) | `temporal_pattern` |

### 9.2 Deviation

`habit_deviation`: `normal` | `elevated_spend` | `new_merchant` | `category_shift`

Compare current receipt to merchant/item baseline (>1.5× avg → `elevated_spend`).

### 9.3 Output

```json
"habits": {
  "repeat_items": [{"name": "Organic milk", "match_count": 4, "cadence_days": 7}],
  "merchant_cadence": {"merchant_key": "…", "typical_interval_days": 7},
  "pattern_label": "weekly_grocery_restock",
  "deviation": "normal",
  "confidence": "high"
}
```

---

## 10. Behavioral Summary Design (RIE-SUM01)

### 10.1 Structured summary (machine)

| Field | Question answered |
|-------|-------------------|
| `what_happened` | Factual 1–2 sentences from header + lines |
| `why_it_happened` | Trip + tags + habit context |
| `is_this_normal` | Compare to merchant/habit baseline |
| `is_this_beneficial` | Essential score + goal alignment (future goals.json) |
| `could_improve` | Top savings suggestion |

### 10.2 User-facing template

Rendered on dashboard receipt detail / post-upload card:

```
What happened: You spent $87.42 at Costco across 12 items, mostly groceries.

Why it happened: This looks like a planned grocery restock (refill), not a convenience stop.

Is this normal? Yes — similar trips every ~7 days; spend is within your usual range.

Is this beneficial? Mostly essential (score 0.71) — aligns with household necessities.

Could improve: Two discretionary snack lines ($8.50) flagged as avoidable on a stock-up trip.
```

### 10.3 Generation

1. **Template fill** from `behavioral_meta` (deterministic, always available).
2. **OpenAI polish** optional (max 120 words) using structured fields only — no free-form inference beyond provided JSON.

### 10.4 Storage

Embed under transaction:

```json
"behavioral_meta": {
  "version": "2.0",
  "essential": { ... },
  "trip": { "trip_type": "grocery_restock", "confidence": "high", ... },
  "behavioral_tags": [ ... ],
  "savings": { ... },
  "merchant_intelligence": { ... },
  "habits": { ... },
  "summary": {
    "what_happened": "...",
    "why_it_happened": "...",
    "is_this_normal": "...",
    "is_this_beneficial": "...",
    "could_improve": "...",
    "confidence": "medium"
  },
  "computed_at": "ISO-8601"
}
```

---

## 11. OpenAI Structured Extension (v2 prompt)

Extend vision or add **second pass** (preferred: second pass on confirmed structured v1 data):

```json
{
  "essential_classification": "mixed",
  "essential_score": 0.58,
  "trip_type": "grocery_restock",
  "behavioral_tags": ["recurring", "convenience"],
  "savings_notes": ["..."],
  "behavioral_summary": {
    "what_happened": "",
    "why_it_happened": "",
    "is_this_normal": "",
    "is_this_beneficial": "",
    "could_improve": ""
  },
  "confidence": "medium"
}
```

Rules engine **merges** with model output (model never sole authority).

---

## 12. UI / Route Impact (IOR-06 preview)

| Surface | Change |
|---------|--------|
| Dashboard | Receipt rows show trip_type badge + essential chip |
| Receipt detail / expand | Full behavioral summary five questions |
| `/upload_receipt` | Post-save flash includes one-line behavioral insight |
| `/insights` | Aggregate behavioral tags + savings themes |
| `/receipt_review` | Optional preview of predicted behavioral labels |

No new route required for MVP v2; optional `/receipt/<id>/behavior` later.

---

## 13. Implementation Plan (ACI-IOR-06)

| Phase | Deliverable | Size |
|-------|-------------|------|
| A | `behavioral_rules.py` + unit tests (no OpenAI) | S |
| B | `BehavioralReceiptIntelligenceService` + `behavioral_meta` persistence | M |
| C | Dashboard + summary template UI | M |
| D | Insights aggregation + optional OpenAI polish | S |
| E | Config lexicons + demo reset clears behavioral cache | S |

**Estimated complexity:** **Medium–High (M/H)** — ~5–8 dev days after restoration export enum reconciliation.

---

## 14. Success Criteria (ACI-IOR-05)

| Criterion | Section |
|-----------|---------|
| Essential model | §4 |
| Trip classification | §5 |
| Behavioral tags | §6 |
| Savings model | §7 |
| Merchant intelligence | §8 |
| Habit detection | §9 |
| Behavioral summary | §10 |
| Design document | This file |

---

## 15. References

- v1: `docs/receipt_intelligence/receipt_intelligence_design.md`
- Implementation: `app/services/receipt_intelligence_service.py`, `app/utils/receipt_normalize.py`
- Authority: `Financial_App_Receipt_Intelligence_Restoration_Export` (ingest when available)
