# ACI-IOR-02 — IOR Hardening Bundle Report

**Project:** Financial App  
**Branch:** `feature/ior-hardening-bundle`  
**Date:** 2026-06-02  
**Status:** COMPLETE (local scope; no merge/deploy)

---

## Summary

Implemented Initial Official Release hardening: Demo Reset (UI + confirmation), standardized OpenAI API key loading (`OPENAI_API_KEY` first, file fallback), modernized insights to OpenAI SDK v1, documentation updates, and local validation. Terraform, AWS, and Docker publish were not modified per scope.

---

## Files Modified

| File | Change |
|------|--------|
| `app/utils/openai_key.py` | **New** — shared key loader (env → file) |
| `app/utils/storage.py` | `reset_demo_data()` for transactions, uploads, goals.json, app.log |
| `app/routes/main.py` | `/demo_reset` GET/POST with confirmation |
| `app/templates/demo_reset.html` | **New** — reset UI and warnings |
| `app/templates/base.html` | Nav link: Demo Reset |
| `app/services/openai_receipt_service.py` | Uses shared key loader |
| `app/services/openai_service.py` | Shared loader + SDK v1 `chat.completions` for insights |
| `app/utils/preflight.py` | Uses shared key loader |
| `tests/test_demo_reset.py` | **New** — unit + route tests |
| `tests/test_openai_key.py` | **New** — env/file precedence tests |
| `tests/test_app_import.py` | Assert `demo_reset` route registered |
| `README.md` | Demo Reset + OpenAI key expectations |
| `docs/DOCKER_USAGE.md` | `OPENAI_API_KEY` preferred for containers |

---

## Demo Reset Behavior

- **Access:** Navigation → **Demo Reset** (`/demo_reset`)
- **Confirmation:** Required checkbox (`confirm=yes`) plus browser `confirm()` dialog on submit
- **Clears:** `data/transactions.json`, files in configured uploads folder, optional `data/goals.json`, `logs/app.log`
- **Preserves:** `config.json`, application source, Terraform, deployment configs
- **Post-reset:** Redirect to dashboard with success flash

---

## OpenAI Key Loading

**Order (all services and preflight):**

1. `OPENAI_API_KEY` environment variable (trimmed)
2. File at `openai.api_key_file` from `config.json`

**Implementation:** `app/utils/openai_key.py` — used by `OpenAIService`, `OpenAIReceiptParsingService`, and `validate_preflight()`.

**Insights:** `OpenAIService.generate_insights()` now uses OpenAI Python SDK v1 (`OpenAI().chat.completions.create`) instead of legacy `ChatCompletion.create`.

Keys are never logged or committed.

---

## Validation Performed

| Check | Method | Result |
|-------|--------|--------|
| Dashboard | Flask test client `GET /` | 200 |
| Transaction entry | `POST /add_transaction` | 200, transaction saved |
| Receipt upload page | `GET /upload_receipt` | 200 |
| Insights page | `GET /insights` | 200 |
| Demo reset page | `GET /demo_reset` | 200 |
| Demo reset execution | `POST` with confirm | Transactions cleared (10 → 0) |
| Receipt parsing | Existing pytest suite | PASS |
| OpenAI key precedence | `tests/test_openai_key.py` | PASS |

Receipt upload/parse and live OpenAI insights were not re-run against the live API in this ACI (requires operator key and image upload); unit tests mock API behavior.

---

## Test Results

```
pytest -v
25 passed in ~4s
```

New tests: `test_demo_reset.py` (3), `test_openai_key.py` (3).

---

## Documentation Updates

- `README.md` — OpenAI key order, Demo Reset section
- `docs/DOCKER_USAGE.md` — prefer `OPENAI_API_KEY` in containers

---

## Blockers

| Blocker | Severity | Notes |
|---------|----------|-------|
| None for ACI-IOR-02 scope | — | Local hardening complete |
| PAPE not declared | External | Out of scope |
| PE EC2 stopped | External | Resume in later ACI |
| Transaction edit/delete | Product | Identified in IOR-01; not in IOR-02 scope |

---

## Recommendations

1. **ACI-IOR-03:** PE validation with EC2 started; verify `OPENAI_API_KEY` via Terraform user-data matches Docker/local behavior.
2. Merge `feature/ior-hardening-bundle` → `deployable` after review; triggers Docker publish on merge.
3. Consider transaction edit/delete as next IOR feature slice.
4. Set GitHub default branch to `deployable` if not already done (IOR-00).

---

## Proceed to ACI-IOR-03?

**Yes**, with the understanding that ACI-IOR-03 should focus on production-environment validation (resume SPE-01, end-to-end flows on PE) rather than repeating local hardening. This bundle satisfies IOR-02 success criteria for demo reset, OpenAI alignment, tests, and documentation.

---

## Scope Compliance

- [x] No Terraform changes
- [x] No AWS / EC2 / deploy actions
- [x] No Docker publish
- [x] No merge to `deployable`
- [x] Branch pushed to origin
