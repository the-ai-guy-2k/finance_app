"""ACI-PE-07 validation for Receipt Intelligence v2 on SPE-01."""
import json
import re
import sys
from io import BytesIO

try:
    import requests
except ImportError:
    print("FAIL: requests not installed")
    sys.exit(1)

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://44.192.97.51"
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
        payload["csrf_token"] = token
    return SESSION.post(
        path, data=payload, files=files, allow_redirects=True, timeout=120
    )


PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def confirm_receipt_review(merchant, lines, total="55.00"):
    """Upload triggers review; confirm with scripted grocery/convenience basket."""
    page = SESSION.get(f"{BASE}/upload_receipt", timeout=30)
    token = extract_csrf(page.text)
    files = {"receipt": ("pe07_test.png", BytesIO(PNG), "image/png")}
    data = {"csrf_token": token} if token else {}
    r = SESSION.post(
        f"{BASE}/upload_receipt",
        data=data,
        files=files,
        allow_redirects=True,
        timeout=120,
    )
    if "/receipt_review/" not in r.url:
        return r, None
    receipt_id = r.url.rstrip("/").split("/")[-1]
    review = SESSION.get(f"{BASE}/receipt_review/{receipt_id}", timeout=30)
    token = extract_csrf(review.text)
    form = {
        "action": "confirm",
        "merchant": merchant,
        "date": "2026-06-04",
        "total": total,
        "payment_method": "credit",
    }
    if token:
        form["csrf_token"] = token
    for idx, line in enumerate(lines):
        form.setdefault("line_name", [])
        form.setdefault("line_total", [])
        form.setdefault("line_category", [])
        if isinstance(form["line_name"], list):
            form["line_name"].append(line["name"])
            form["line_total"].append(line["total"])
            form["line_category"].append(line["category"])
        else:
            pass
    # requests needs list of tuples for repeated keys
    items = [(k, v) for k, v in form.items() if k not in ("line_name", "line_total", "line_category")]
    for i in range(len(lines)):
        items.append(("line_name", lines[i]["name"]))
        items.append(("line_total", lines[i]["total"]))
        items.append(("line_category", lines[i]["category"]))
    r2 = SESSION.post(
        f"{BASE}/receipt_review/{receipt_id}",
        data=items,
        allow_redirects=True,
        timeout=120,
    )
    return r2, receipt_id


# 1 Reachability
try:
    r = SESSION.get(f"{BASE}/", timeout=30)
    ok("reachability", r.status_code == 200, f"GET / -> {r.status_code}")
except Exception as e:
    ok("reachability", False, str(e))
    sys.exit(1)

html = r.text

# 2 Dashboard v2 UI
ok(
    "dashboard_v2_ui",
    "Behavior" in html and "trip-badge" in html and "essential-badge" in html,
    "Behavior column + badges present",
)

# 3 Upload page
try:
    up = SESSION.get(f"{BASE}/upload_receipt", timeout=30)
    ok(
        "upload_receipt",
        up.status_code == 200 and "Receipt Intelligence" in up.text,
        "upload page OK",
    )
except Exception as e:
    ok("upload_receipt", False, str(e))

# 4 Insights behavioral section marker (empty state ok)
try:
    ins = SESSION.get(f"{BASE}/insights", timeout=120)
    has_ctx = "Behavioral Insights" in ins.text or "Category context" in ins.text
    has_behavioral_section = (
        "Receipt behavioral context" in ins.text
        or "behavioral" in ins.text.lower()
    )
    ok(
        "insights_page",
        ins.status_code == 200 and has_ctx,
        f"status={ins.status_code} behavioral_section={has_behavioral_section}",
    )
except Exception as e:
    ok("insights_page", False, str(e))

# 5 Demo reset
try:
    post_with_csrf(f"{BASE}/demo_reset", {"confirm": "yes"})
    dash = SESSION.get(f"{BASE}/", timeout=30)
    ok("demo_reset", dash.status_code == 200, "reset submitted")
except Exception as e:
    ok("demo_reset", False, str(e))

# 6 Grocery receipt -> behavioral on dashboard
grocery_lines = [
    {"name": "Milk", "total": "4.00", "category": "groceries"},
    {"name": "Bread", "total": "3.00", "category": "groceries"},
    {"name": "Eggs", "total": "5.00", "category": "groceries"},
    {"name": "Rice", "total": "6.00", "category": "groceries"},
    {"name": "Chicken", "total": "32.00", "category": "groceries"},
]
try:
    r_g, _ = confirm_receipt_review("Kroger Grocery", grocery_lines, total="50.00")
    dash = SESSION.get(f"{BASE}/", timeout=30)
    has_trip = "Grocery" in dash.text or "grocery" in dash.text.lower()
    has_essential = "Essential" in dash.text or "essential" in dash.text.lower()
    has_summary = "Behavioral summary" in dash.text or "behavioral-summary" in dash.text
    has_meta_signals = has_trip and has_essential and has_summary
    ok(
        "grocery_receipt_behavioral",
        r_g.status_code == 200 and has_meta_signals,
        f"redirect_ok={r_g.status_code==200} trip={has_trip} essential={has_essential} summary={has_summary}",
    )
except Exception as e:
    ok("grocery_receipt_behavioral", False, str(e))

# 7 Convenience receipt
conv_lines = [
    {"name": "Snacks", "total": "6.00", "category": "shopping"},
    {"name": "Soda", "total": "4.00", "category": "shopping"},
]
try:
    r_c, _ = confirm_receipt_review("7-Eleven", conv_lines, total="10.00")
    dash = SESSION.get(f"{BASE}/", timeout=30)
    has_convenience = (
        "Convenience" in dash.text or "convenience" in dash.text.lower()
    )
    ok(
        "convenience_receipt_behavioral",
        r_c.status_code == 200 and has_convenience,
        f"convenience_signals={has_convenience}",
    )
except Exception as e:
    ok("convenience_receipt_behavioral", False, str(e))

# 8 Insights after receipts
try:
    ins2 = SESSION.get(f"{BASE}/insights", timeout=120)
    behavioral_ctx = "Receipt behavioral context" in ins2.text
    ok(
        "insights_behavioral_context",
        ins2.status_code == 200 and behavioral_ctx,
        f"behavioral_context_block={behavioral_ctx}",
    )
except Exception as e:
    ok("insights_behavioral_context", False, str(e))

# 9 Legacy manual tx (no behavioral_meta) - add manual, should not break
try:
    post_with_csrf(
        f"{BASE}/add_transaction",
        {
            "merchant": "PE07_Legacy_Manual",
            "amount": "9.99",
            "category": "other",
            "date": "2026-06-04",
        },
    )
    dash = SESSION.get(f"{BASE}/", timeout=30)
    ok(
        "legacy_manual_compat",
        "PE07_Legacy_Manual" in dash.text,
        "manual transaction visible",
    )
except Exception as e:
    ok("legacy_manual_compat", False, str(e))

print("\n=== SUMMARY ===")
all_pass = all(v["pass"] for v in RESULTS.values())
for k, v in RESULTS.items():
    print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}")
print(f"OVERALL: {'PASS' if all_pass else 'PARTIAL/FAIL'}")
sys.exit(0 if all_pass else 1)
