"""Basic HAAL usage: encode, decode, validate.

Run: python examples/basic_usage.py
"""

import haaland
from haaland.errors import HaalDecodeError

data = {
    "users": [
        {"id": 1, "name": "Ada Lovelace", "role": "admin", "active": True},
        {"id": 2, "name": "Grace Hopper", "role": "editor", "active": True},
        {"id": 3, "name": "Alan Turing", "role": "viewer", "active": False},
    ],
    "meta": {"generated": "2026-07-14", "source": "examples"},
}

text = haaland.dumps(data)
print("--- HAAL ---")
print(text)

assert haaland.loads(text) == data
print("\nround-trip: OK")

# Strict validation: losing a table row is a located error, not silent data loss.
lines = text.splitlines()
truncated = "\n".join(lines[:3] + lines[4:])  # drop one of the 3 declared rows
try:
    haaland.loads(truncated)
    raise AssertionError("expected HaalDecodeError")
except HaalDecodeError as e:
    print(f"truncation detected: {e}")
