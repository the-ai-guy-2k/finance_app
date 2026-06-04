# ACI-IOR-06 — Behavioral Receipt Intelligence Implementation

**ACI:** ACI-IOR-06  
**Branch:** `feature/receipt-intelligence-v2`  
**Date:** 2026-06-02  
**Status:** Implementation complete (stop point — no merge, deploy, or PE validation)

---

## 1. Summary

Receipt Intelligence v2 adds a **rules-first behavioral layer** on top of v1 receipt parsing. After a receipt transaction is confirmed (auto-commit or review), `behavioral_meta` is computed from line items, merchant history, and deterministic heuristics, then persisted on the parent transaction.

Design authority: `docs/receipt_intelligence/receipt_intelligence_v2_design.md`

**Restoration export:** `Financial_App_Receipt_Intelligence_Restoration_Export` was not present in the repository; no export file was added.

---

## 2. Success Criteria

| Criterion | Status |
|-----------|--------|
| Essential scoring works | ✅ |
| Trip classification works | ✅ |
| Behavioral tags work | ✅ |
| Savings indicators work | ✅ |
| Merchant tracking works | ✅ |
| Habit detection works | ✅ |
| Dashboard updated | ✅ |
| Insights updated | ✅ |
| Backward compatibility maintained | ✅ |
| Tests pass | ✅ (`pytest -v` — 55 passed) |
| Report created | ✅ |

---

## 3. Branch and Files

### Branch

`feature/receipt-intelligence-v2`

### New files

| Path | Role |
|------|------|
| `app/services/behavioral_receipt_intelligence_service.py` | v2 orchestration |
| `app/utils/behavioral_rules.py` | Essential, trip, tags, habits, savings, summary |
| `app/utils/behavioral_normalize.py` | Enums, labels, score clamping |
| `app/utils/merchant_memory.py` | Rolling merchant profiles |
| `tests/test_behavioral_rules.py` | Rule unit tests |
| `tests/test_behavioral_receipt_intelligence_service.py` | Service + compat tests |
| `tests/test_dashboard_stats_behavioral.py` | Summary/insights context |
| `reports/aci_ior/aci_ior_06_behavioral_receipt_intelligence_implementation.md` | This report |

### Modified files

| Path | Change |
|------|--------|
| `app/services/receipt_intelligence_service.py` | `attach_behavioral()` hook |
| `app/routes/main.py` | Behavioral enrich on commit; template helpers |
| `app/utils/dashboard_stats.py` | `behavioral_rows`, insights context |
| `app/services/openai_service.py` | Behavioral context in insights prompt |
| `app/templates/dashboard.html` | Trip/essential badges, summary panel |
| `app/templates/insights.html` | Behavioral context section |
| `config.docker.example.json` | `behavioral_intelligence` thresholds |

---

## 4. New Behavioral Fields (`behavioral_meta`)

Attached to receipt-sourced transactions only:

```json
{
  "version": "2.0",
  "computed_at": "<ISO8601 UTC>",
  "essential_score": 0.82,
  "essential": {
    "essential_score": 0.82,
    "non_essential_score": 0.18,
    "classification": "essential|non_essential|discretionary|mixed|unknown",
    "confidence": "high|medium|low",
    "reason_codes": [],
    "line_spread": 0.12
  },
  "trip": {
    "trip_type": "grocery_restock|convenience_run|refill_trip|impulse_purchase|maintenance_purchase|emergency_purchase|mixed_basket|unknown",
    "confidence": "high|medium|low",
    "trip_confidence": "high|medium|low",
    "reason_codes": []
  },
  "behavioral_tags": [
    {"tag": "convenience", "strength": 0.9, "confidence": "medium"}
  ],
  "savings": {
    "opportunities": [{"type": "...", "severity": "...", "message": "..."}],
    "avoidable_spend_indicators": [],
    "convenience_spend_detected": false
  },
  "merchant_intelligence": {
    "merchant_key": "...",
    "visit_count": 3,
    "avg_basket": 42.5,
    "dominant_trip_type": "grocery_restock",
    "behavior_summary": "..."
  },
  "habits": {
    "repeat_merchant": true,
    "repeat_categories": [],
    "repeat_items": [],
    "spending_pattern_indicators": [],
    "merchant_visit_count_prior": 2
  },
  "summary": {
    "what_happened": "...",
    "why": "...",
    "is_it_normal": "...",
    "is_it_beneficial": "...",
    "could_it_improve": "...",
    "narrative_short": "..."
  },
  "confidence": "high|medium|low",
  "reason_codes": []
}
```

Older transactions without `behavioral_meta` continue to load and render (dashboard shows “v1 only” for receipt rows).

---

## 5. Dashboard Changes

- New **Behavior** column: trip type badge + essential/non-essential indicator.
- Expandable **Behavioral summary** row per receipt (what / why / normal / beneficial / improve).
- Savings opportunity bullets when flagged.
- Summary card: **Behavioral receipts** count.

---

## 6. Insight Changes

- `build_insights_context()` includes `behavioral_summaries` and per-receipt `behavioral` block.
- OpenAI insights prompt includes v2 behavioral snapshots.
- Heuristic fallback mentions trip types when behavioral data exists.
- Insights page: **Receipt behavioral context** list (trip + essential + short narrative).

---

## 7. Test Results

```
pytest -v
55 passed, 3 warnings in 6.78s
```

New tests: 12 (behavioral rules, service, dashboard behavioral).

---

## 8. Blockers

| Blocker | Impact | Mitigation |
|---------|--------|------------|
| Restoration export file missing | Cannot reconcile enum IDs verbatim with export | Design doc + RIE map used; add export to `docs/receipt_intelligence/` when available |
| Optional OpenAI behavioral enrichment not implemented | v2 is rules-only | Matches design “rules-first”; AI merge deferred |
| Existing receipts lack `behavioral_meta` until re-upload | Historical receipts show v1-only UI | PA-07 could add optional backfill script if desired |

---

## 9. Recommendation for ACI-PA-07

1. **Merge** `feature/receipt-intelligence-v2` → `deployable` via fast-forward or PR after review.
2. **CI / Docker:** Confirm GitHub Actions pass and publish image tag on `deployable` push.
3. **Config:** Propagate `behavioral_intelligence` block to production `config.json` / secrets as needed.
4. **Optional backfill:** One-off job to run `BehavioralReceiptIntelligenceService.enrich_transaction()` over existing `source=receipt` rows (not required for launch).
5. **Closeout report:** `reports/aci_pa/aci_pa_07_receipt_intelligence_v2_closeout.md` with Hub digest and merge SHA.
6. **Handoff PE-07:** Pin new image on SPE-01; validate dashboard behavioral badges and insights context on host.

---

## 10. Stop Point Compliance

- ✅ Implementation on feature branch  
- ❌ No merge to `deployable`  
- ❌ No deploy / Terraform / PE validation  

---

*End of ACI-IOR-06 implementation report.*
