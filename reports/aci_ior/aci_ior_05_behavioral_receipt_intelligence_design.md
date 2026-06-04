# ACI-IOR-05 — Behavioral Receipt Intelligence Design

**Project:** Financial App  
**Date:** 2026-06-04  
**Scope:** Design only — no code changes  
**Branch:** `feature/receipt-intelligence-v2`  
**Authority:** `Financial_App_Receipt_Intelligence_Restoration_Export` (ACI-specified)

---

## Executive Summary

Receipt Intelligence **v2** adds a **behavioral intelligence layer** on top of v1’s extraction pipeline. v1 answers *what was purchased*; v2 answers *why*, *what it means*, and *what behavior it represents*. Design follows restoration export concept areas (RIE-E01 through RIE-SUM01), rules-first + AI-enhanced architecture, and extends the v1 parent transaction with `behavioral_meta`.

**Restoration export file:** Not found in repo at design time; full spec in `docs/receipt_intelligence/receipt_intelligence_v2_design.md` with reconciliation note when export is ingested.

---

## 1. Behavioral Model

**Pattern:** Post-commit pipeline — after v1 saves `line_items[]` + `receipt_meta`, run history-aware rules + optional structured OpenAI pass → attach `behavioral_meta` to transaction.

**Principles:** Explainable (`reason_codes`), confidence on all labels, backward compatible (no `behavioral_meta` = v1 UI).

**New modules (IOR-06):** `BehavioralReceiptIntelligenceService`, `behavioral_rules.py`, `behavioral_normalize.py`, `merchant_memory.py`.

---

## 2. Essential / Non-Essential Model

| Element | Design |
|---------|--------|
| **Classification** | `essential`, `non_essential`, `discretionary`, `mixed`, `unknown` |
| **Scoring** | Per-line 0–1 essential score → amount-weighted receipt score |
| **Confidence** | `high` / `medium` / `low` from line confidence, merchant prior, keyword coverage |
| **Thresholds** | Config: 0.75 essential, 0.35 non-essential, 0.40 mixed spread |

---

## 3. Trip Classification Model

| `trip_type` | Intent |
|-------------|--------|
| `grocery_restock` | Planned stock-up |
| `convenience_run` | Small/quick top-up |
| `refill_trip` | Repeat consumables |
| `impulse_purchase` | Unplanned discretionary |
| `maintenance_purchase` | Upkeep |
| `emergency_purchase` | Urgent necessity |
| `mixed_basket` | Competing intents |
| `unknown` | Fallback |

**Logic:** Rule scores per type (merchant list, basket size, line match history, essential profile); winner ≥0.45 or `mixed_basket`; AI assist merged when confidence sufficient.

---

## 4. Behavioral Tag Model

**Multi-select tags:** `convenience`, `impulse`, `recurring`, `luxury`, `maintenance`, `social`, `health`, `productivity`.

Each tag: `strength` 0–1, `confidence`, `reason`. Triggered by lexicon + trip/essential cross-signals + model.

---

## 5. Savings Model

| Method | Output |
|--------|--------|
| Convenience cost detection | `convenience_premium_estimate` |
| Recurring spend awareness | `recurring_spend_alert`, annualized estimate |
| Avoidable spend | `avoidable_spend_total` (impulse + non-essential lines) |
| Category concentration | `concentration_warning` (>40% 30d in one category) |

`savings_opportunity_score` + human-readable `suggestions[]`.

---

## 6. Merchant Model

Rolling 30d profile per merchant: visit count, avg basket, essential bias, dominant trip type.

`merchant_behavior_score` + `pattern_label` (e.g. `stable_restock`, `discretionary_heavy`).

---

## 7. Habit Model

Detect: repeat items (fuzzy name match), repeat merchants (cadence), repeat categories (spend share), temporal patterns.

`habit_deviation`: `normal` | `elevated_spend` | `new_merchant` | `category_shift`.

---

## 8. Behavioral Summary Design

Five questions (restoration SUM01):

1. **What happened?** — factual
2. **Why it happened?** — trip + tags + habits
3. **Is this normal?** — baseline comparison
4. **Is this beneficial?** — essential alignment
5. **Could it be improved?** — top savings opportunity

Delivery: structured JSON + template-rendered user text; optional OpenAI polish (≤120 words) from structured fields only.

---

## 9. Estimated Implementation Complexity

| Rating | **Medium–High (M/H)** |
|--------|------------------------|
| Effort | ~5–8 dev days (IOR-06) |
| Risk | Medium — depends on history depth and lexicon quality |
| Prerequisite | Ingest restoration export enums into config when file available |

---

## 10. Recommendation for ACI-IOR-06

1. Add `Financial_App_Receipt_Intelligence_Restoration_Export` to `docs/receipt_intelligence/` and reconcile enums (1:1 with §4–10 in v2 design doc).
2. Implement **Phase A** rules-only `behavioral_meta` (no OpenAI) + tests.
3. Wire into `ReceiptIntelligenceService` post-commit (auto + review confirm paths).
4. Dashboard: trip badge, essential chip, expandable five-question summary.
5. Extend insights with tag/savings aggregates.
6. Branch: `feature/receipt-intelligence-v2`; do not merge until PA-07.

---

## 11. Success Criteria

| Criterion | Status |
|-----------|--------|
| Essential model designed | Pass |
| Trip classification designed | Pass |
| Behavioral tags designed | Pass |
| Savings model designed | Pass |
| Merchant intelligence designed | Pass |
| Habit detection designed | Pass |
| Behavioral summary designed | Pass |
| Design document created | Pass |
| Report created | Pass |

---

## Scope Compliance

- [x] Design only — no implementation
- [x] v2 behavioral layer defined atop v1
- [x] Restoration export concepts organized (RIE map)
- [x] Ready for IOR-06
