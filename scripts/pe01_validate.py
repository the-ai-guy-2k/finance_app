"""ACI-PE-01 HTTP validation against SPE-01 (no secrets printed)."""
import re
import sys
from io import BytesIO

try:
    import requests
except ImportError:
    print("FAIL: requests not installed")
    sys.exit(1)

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://44.197.147.63"
SESSION = requests.Session()
RESULTS = {}


def ok(name, passed, detail=""):
    RESULTS[name] = {"pass": passed, "detail": detail}
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}: {detail}")


def extract_csrf(html):
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return match.group(1) if match else None


def post_with_csrf(path, data=None, files=None):
    page = SESSION.get(path, timeout=30)
    token = extract_csrf(page.text)
    payload = dict(data or {})
    if token:
        payload['csrf_token'] = token
    return SESSION.post(path, data=payload, files=files, allow_redirects=True, timeout=120)


# 1. Reachability
try:
    r = SESSION.get(f"{BASE}/", timeout=30)
    ok("reachability", r.status_code == 200, f"GET / -> {r.status_code}")
except Exception as e:
    ok("reachability", False, str(e))
    print("\n=== SUMMARY ===")
    sys.exit(1)

# 2. Dashboard
html = r.text
ok(
    "dashboard",
    r.status_code == 200 and "Financial Nebula Node" in html,
    f"len={len(html)}",
)

# 3. Transaction entry
merchant = "PE01_Validation_Merchant"
try:
    post_with_csrf(
        f"{BASE}/add_transaction",
        {
            "merchant": merchant,
            "amount": "42.50",
            "category": "validation",
            "date": "2026-06-04",
            "note": "ACI-PE-01 test transaction",
        },
    )
    dash = SESSION.get(f"{BASE}/", timeout=30)
    found = merchant in dash.text
    ok("transaction", dash.status_code == 200 and found, f"merchant visible={found}")
except Exception as e:
    ok("transaction", False, str(e))

# 4. Receipt upload (minimal PNG)
png = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)
try:
    page = SESSION.get(f"{BASE}/upload_receipt", timeout=30)
    token = extract_csrf(page.text)
    files = {"receipt": ("pe01_test.png", BytesIO(png), "image/png")}
    data = {"csrf_token": token} if token else {}
    r = SESSION.post(
        f"{BASE}/upload_receipt",
        data=data,
        files=files,
        allow_redirects=True,
        timeout=120,
    )
    ok("receipt_upload", r.status_code == 200, f"POST upload_receipt -> {r.status_code}")
except Exception as e:
    ok("receipt_upload", False, str(e))

# 5. AI insights
try:
    r = SESSION.get(f"{BASE}/insights", timeout=120)
    text = r.text
    heuristic = "heuristic" in text.lower() or "Full insights require OpenAI" in text
    ok(
        "ai_insights",
        r.status_code == 200 and not heuristic,
        f"status={r.status_code} heuristic_only={heuristic} has_content={len(text)>500}",
    )
except Exception as e:
    ok("ai_insights", False, str(e))

# 6. Demo reset
try:
    r = SESSION.get(f"{BASE}/demo_reset", timeout=30)
    has_form = "confirm" in r.text and "Reset Demo Data" in r.text
    token = extract_csrf(r.text)
    r2 = SESSION.post(
        f"{BASE}/demo_reset",
        data={"confirm": "yes", "csrf_token": token} if token else {"confirm": "yes"},
        allow_redirects=True,
        timeout=30,
    )
    dash = SESSION.get(f"{BASE}/", timeout=30)
    merchant_gone = merchant not in dash.text
    dash_ok = dash.status_code == 200 and "Financial Nebula Node" in dash.text
    ok(
        "demo_reset",
        has_form and r2.status_code == 200 and merchant_gone and dash_ok,
        f"form={has_form} merchant_cleared={merchant_gone} dash_ok={dash_ok}",
    )
except Exception as e:
    ok("demo_reset", False, str(e))

# 7. Post-reset transaction (usability)
try:
    post_with_csrf(
        f"{BASE}/add_transaction",
        {"merchant": "PE01_PostReset", "amount": "1.00", "category": "test"},
    )
    dash = SESSION.get(f"{BASE}/", timeout=30)
    ok(
        "post_reset_usability",
        "PE01_PostReset" in dash.text,
        "transaction after reset",
    )
except Exception as e:
    ok("post_reset_usability", False, str(e))

# 8. CSRF enforcement smoke test
try:
    r = SESSION.post(
        f"{BASE}/add_transaction",
        data={"merchant": "NoCSRF", "amount": "1.00"},
        allow_redirects=False,
        timeout=30,
    )
    ok("csrf_enforced", r.status_code == 400, f"bare POST -> {r.status_code}")
except Exception as e:
    ok("csrf_enforced", False, str(e))

print("\n=== SUMMARY ===")
all_pass = all(v["pass"] for v in RESULTS.values())
for k, v in RESULTS.items():
    print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}")
print(f"OVERALL: {'PASS' if all_pass else 'PARTIAL/FAIL'}")
sys.exit(0 if all_pass else 1)
