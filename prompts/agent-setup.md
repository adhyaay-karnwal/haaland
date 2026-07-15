# Agent setup prompt

Paste the prompt below into your AI coding agent (Claude Code, Cursor, Copilot
Workspace, etc.) to have it integrate HAAL into your codebase. It is written to keep
the agent conservative: measure first, convert only the payloads where HAAL wins, and
prove losslessness with tests.

---

```
Integrate the HAAL serialization format (https://github.com/adhyaay-karnwal/haaland)
into this codebase to reduce LLM token costs. Work in a branch. Follow these steps
exactly and do not skip the measurement steps:

1. Install: pip install "haaland[tokens] @ git+https://github.com/adhyaay-karnwal/haaland.git"
   (Python only for now; if this codebase is not Python, stop and report that.)

2. Find every place where structured data is serialized into an LLM prompt or
   context window (search for json.dumps, yaml.dump, and string-formatted tables
   near LLM API calls). List them with file:line.

3. For each site, extract or construct a representative sample payload and run:
   haal stats sample.json
   Record the measured savings. Only convert sites where HAAL saves >= 10% tokens;
   leave the rest as JSON and note why.

4. For each site being converted:
   a. Replace json.dumps(data) with haaland.dumps(data).
   b. Add the HAAL syntax primer from prompts/system-prompt.md in the HAAL repo to
      the system prompt ONCE (not per message).
   c. If the model's OUTPUT is parsed as JSON anywhere downstream, do NOT change the
      output side unless asked — HAAL input and JSON output can coexist.

5. Add a round-trip test for each converted payload type:
   assert haaland.loads(haaland.dumps(payload)) == payload

6. Run the project's test suite and the new tests.

7. Report: sites found, sites converted vs skipped (with measured percentages),
   and the total measured token reduction on the sample payloads.

Do not fabricate savings numbers; every percentage in your report must come from a
haal stats run you actually executed.
```

---

## For platform/infra teams

If you want a drop-in shim instead of per-site edits, wrap your prompt-assembly
layer:

```python
import haaland, json

def to_context(data, *, threshold=0.10):
    """Serialize for LLM context; picks HAAL when it saves >= threshold tokens."""
    from haaland.tokens import count_tokens
    j = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    h = haaland.dumps(data)
    if count_tokens(h) <= count_tokens(j) * (1 - threshold):
        return h, "haal"
    return j, "json"
```

This keeps the decision empirical per payload — the same policy our benchmarks
recommend, since HAAL wins on record-shaped data and compact JSON wins on small
deep objects.
