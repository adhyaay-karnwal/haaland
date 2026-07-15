"""Build an LLM prompt with HAAL-serialized records and measure the savings.

Run: pip install "haaland[tokens]" then python examples/llm_context.py
"""

import json

import haaland
from haaland.tokens import compare

events = [
    {"id": 9000001 + i, "type": t, "repo": r, "ok": True}
    for i, (t, r) in enumerate(
        [("push", "core/api"), ("release", "core/web"), ("fork", "ml/training")] * 20
    )
]
payload = {"events": events}

prompt_haal = (
    "Here are recent events:\n\n" + haaland.dumps(payload) + "\n\nWhich repository was most active?"
)
prompt_json = (
    "Here are recent events:\n\n"
    + json.dumps(payload, indent=2)
    + "\n\nWhich repository was most active?"
)

results = compare({"json": prompt_json, "haal": prompt_haal})
for name, r in results.items():
    print(f"{name:5} {r['tokens']:6,} tokens  ({r['vs_json_pct']:+.1f}% vs JSON)")

# Note: the "json" baseline here is pretty-printed, as commonly pasted into
# prompts. See benchmarks/ for compact-JSON baselines.
