# Quickstart

Five minutes from install to measured savings.

## 1. Install

```bash
pip install "haaland[tokens] @ git+https://github.com/adhyaay-karnwal/haaland.git"
```

Requires Python 3.10+. The `[tokens]` extra pulls in `tiktoken` for the `haal stats`
command; the core codec has zero dependencies.

## 2. Convert something

```bash
echo '{"tasks":[{"id":1,"title":"write docs","done":false},{"id":2,"title":"ship","done":true}]}' | haal encode
```

```
tasks[2]{id,title,done}:
 1,write docs,false
 2,ship,true
```

Round-trip it back:

```bash
echo '{"tasks":[{"id":1,"title":"write docs","done":false}]}' | haal encode | haal decode
```

## 3. Measure your own savings

Don't trust our benchmarks — run yours:

```bash
haal stats your_payload.json
```

```
tokenizer: o200k_base
  json              4,732 tokens
  json (2-space)    7,436 tokens  (-57.1% vs JSON)
  haal              3,107 tokens  (+34.3% vs JSON)
  haal (dense)      2,863 tokens  (+39.5% vs JSON)
```

(Output above is the real result for `benchmarks/` dataset `employees_100`.)

## 4. Use it in Python

```python
import haaland

# Encode anything JSON-representable
text = haaland.dumps({"users": [{"id": 1, "name": "Ada"}]})

# Decode with strict validation — truncated or malformed documents raise
# HaalDecodeError with a line number
data = haaland.loads(text)

# File I/O mirrors the json module
with open("data.haal", "w") as f:
    haaland.dump(data, f)
```

## 5. Use it in a prompt

Replace the JSON blob in your prompt with HAAL and add one short system-prompt block
so the model knows the syntax. Copy it from
[`prompts/system-prompt.md`](../prompts/system-prompt.md). Minimal version:

```python
import haaland

SYSTEM = open("prompts/system-prompt.md").read()   # HAAL syntax primer
records = fetch_records()                          # your data

prompt = f"Here are today's records:\n\n{haaland.dumps({'records': records})}\n\nSummarize anomalies."
```

In practice, models read HAAL's tabular form the way they read CSV or markdown tables —
formats heavily represented in training data. For payloads where model *comprehension*
is critical, A/B against JSON on your own eval set before rolling out
(see [llm-integration.md](llm-integration.md#evaluating-comprehension)).

## 6. Validate LLM-emitted HAAL

If you ask a model to *produce* HAAL, the `[N]` length markers make truncation
detectable:

```python
import haaland
from haaland.errors import HaalDecodeError

try:
    data = haaland.loads(model_output)
except HaalDecodeError as e:
    # e.g. "line 12: table declared 50 rows but has 31" -> retry / repair
    retry_with_error_feedback(str(e))
```

## Next steps

- [format-by-example.md](format-by-example.md) — the whole syntax, side by side with JSON
- [llm-integration.md](llm-integration.md) — prompt patterns and validation loops
- [../benchmarks/RESULTS.md](../benchmarks/RESULTS.md) — full measured results
