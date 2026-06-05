"""Single-shot receipt behavioral test against SPE-01."""
import re
import sys
from io import BytesIO

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://44.192.97.51"
S = requests.Session()
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None


def demo_reset():
    p = S.get(f"{BASE}/demo_reset", timeout=30)
    t = csrf(p.text)
    S.post(f"{BASE}/demo_reset", data={"confirm": "yes", "csrf_token": t}, timeout=30)


def upload_and_confirm(merchant, lines, total):
    p = S.get(f"{BASE}/upload_receipt", timeout=30)
    t = csrf(p.text)
    r = S.post(
        f"{BASE}/upload_receipt",
        data={"csrf_token": t} if t else {},
        files={"receipt": ("pe07_test.png", BytesIO(PNG), "image/png")},
        allow_redirects=True,
        timeout=120,
    )
    print("upload_url", r.url)
    if "/receipt_review/" not in r.url:
        return r.url
    rid = r.url.rstrip("/").split("/")[-1]
    p2 = S.get(f"{BASE}/receipt_review/{rid}", timeout=30)
    t2 = csrf(p2.text)
    items = [
        ("action", "confirm"),
        ("merchant", merchant),
        ("date", "2026-06-04"),
        ("total", total),
        ("payment_method", "credit"),
        ("csrf_token", t2),
    ]
    for line in lines:
        items.append(("line_name", line["name"]))
        items.append(("line_total", line["total"]))
        items.append(("line_category", line["category"]))
    r2 = S.post(f"{BASE}/receipt_review/{rid}", data=items, allow_redirects=True, timeout=120)
    print("confirm_url", r2.url)
    return r2.url


if __name__ == "__main__":
    demo_reset()
    grocery = [
        {"name": "Milk", "total": "4.00", "category": "groceries"},
        {"name": "Bread", "total": "3.00", "category": "groceries"},
        {"name": "Eggs", "total": "5.00", "category": "groceries"},
        {"name": "Rice", "total": "6.00", "category": "groceries"},
        {"name": "Chicken", "total": "32.00", "category": "groceries"},
    ]
    upload_and_confirm("Kroger Grocery", grocery, "50.00")
    dash = S.get(f"{BASE}/", timeout=30).text
    print("Kroger", "Kroger" in dash)
    print("trips", re.findall(r"trip-badge[^>]*>([^<]+)", dash))
    conv = [
        {"name": "Snacks", "total": "6.00", "category": "shopping"},
        {"name": "Soda", "total": "4.00", "category": "shopping"},
    ]
    upload_and_confirm("7-Eleven", conv, "10.00")
    dash2 = S.get(f"{BASE}/", timeout=30).text
    print("7-Eleven", "7-Eleven" in dash2 or "7-Eleven" in dash2)
    print("trips2", re.findall(r"trip-badge[^>]*>([^<]+)", dash2))
