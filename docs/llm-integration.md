# LLM integration guide

How to use HAAL with language models in production: patterns for sending data in,
getting data out, validating, and evaluating.

## Pattern 1: HAAL in, prose out (lowest risk, most common)

You serialize records into the context; the model answers in natural language.

```python
import haaland
from pathlib import Path

HAAL_PRIMER = Path("prompts/system-prompt.md").read_text()  # from this repo

system = f"You are an analytics assistant.\n\n{HAAL_PRIMER}"
user = f"""Here are this week's events:

{haaland.dumps({"events": events})}

Which repositories had unusual activity?"""
```

Notes:

- Put the primer in the **system prompt once**, not in every user message.
- If you use prompt caching, the primer is stable content — place it before the
  cache breakpoint so it is cached with the rest of your system prompt.
- The savings apply to every request that carries data; the primer cost is paid once
  per cached prefix.

## Pattern 2: HAAL in, JSON out

Model input is HAAL; model output stays JSON (e.g. because you use your provider's
structured-output / JSON-schema enforcement). These compose fine — nothing about
consuming HAAL requires producing it. This is the recommended pattern when your
platform offers schema-enforced outputs: **never trade away server-side output
validation for token savings on the output side.** Output tokens are also priced
higher than input tokens on every major API, but they are usually a small fraction
of a data-heavy request.

## Pattern 3: HAAL out, validated (for bulk extraction)

When you need the model to emit many records (extraction, classification at scale),
HAAL's declared lengths give you a validation loop JSON can't match:

```python
import haaland
from haaland.errors import HaalDecodeError

def extract(llm, text, max_retries=2):
    prompt = f"""Extract all invoice line items from the document below.
Respond with ONLY a HAAL document of the form:

items[N]{{date,vendor,amount,currency}}:
 <one row per item>

Set N to the exact number of rows.

Document:
{text}"""
    for attempt in range(max_retries + 1):
        out = llm(prompt)
        try:
            return haaland.loads(out.strip())
        except HaalDecodeError as e:
            # The error is precise ("line 12: table declared 8 rows but has 5"),
            # which makes repair prompts effective.
            prompt += f"\n\nYour previous output was invalid HAAL: {e}. Emit the corrected document only."
    raise ValueError("model failed to produce valid HAAL")
```

Why this works: a truncated JSON array is often *silently* valid after repair
heuristics; a truncated HAAL table is a **hard, located error** because the header
declared the row count. Structural drift (a row with a missing cell) is likewise
caught at the exact line.

## Pattern 4: Tool results and agent scratchpads

Agent frameworks spend most of their tokens on tool results. If a tool returns
record-shaped data, serialize the result as HAAL before appending it to the
transcript:

```python
def tool_result_to_context(result) -> str:
    if isinstance(result, (dict, list)):
        return haaland.dumps(result)
    return str(result)
```

Measured on our `events_200` dataset this is a 46.5% reduction per tool result
(dense profile); over a
long agent loop where the transcript is re-sent every turn, savings compound with
turn count (an N-turn loop re-reads earlier results ~N times, so the saving on a
result compounds roughly N times — subject to your provider's prompt caching).

## Evaluating comprehension

Token savings only matter if answer quality holds. We deliberately make **no
unmeasured claims about model comprehension of HAAL** — accuracy depends on your
model, task, and data shape. Before rolling out:

1. Take a representative eval set (even 50 examples).
2. Run it twice — data as compact JSON vs. data as HAAL + primer.
3. Compare task accuracy and token usage.

The tabular form resembles CSV and markdown tables, which are abundant in training
corpora; the nested list form is more novel. If your payloads are mostly nested
(where HAAL's token savings are small anyway), the honest move is often to stay on
JSON. Publish your results — we will link independent evaluations from the README.

## Token accounting checklist

- Measure with **your provider's counter** (`count_tokens` API for Anthropic;
  tiktoken for OpenAI), not a generic estimate. `haal stats` covers the OpenAI side;
  `benchmarks/run_anthropic.py` covers Claude with your API key.
- Count the primer against the savings: `savings_per_request × requests ≫ primer_cost`
  is almost always true with prompt caching, but verify for low-volume paths.
- Remember output pricing ≠ input pricing; compute them separately.
