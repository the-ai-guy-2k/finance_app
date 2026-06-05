import json
import sys
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://44.192.97.51"
# Indirect: parse dashboard for merchants (transactions not exposed as JSON API)
r = requests.get(BASE + "/", timeout=30)
print("len", len(r.text))
for needle in ("Kroger", "7-Eleven", "Grocery Restock", "Convenience", "Behavioral summary", "trip-badge", "essential-badge", "v1 only"):
    print(needle, needle in r.text)
