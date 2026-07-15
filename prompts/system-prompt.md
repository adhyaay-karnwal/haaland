# HAAL system-prompt block

Paste the block below into your system prompt when you pass HAAL-formatted data to a
model, or when you want the model to emit HAAL. It is deliberately short — 344 tokens as
committed, measured under `o200k_base` — and for most payloads the one-time cost is
repaid many times over by the per-request savings on the data itself.

---

```
Data in this conversation may use HAAL, a compact serialization of the JSON data
model. Rules:

- `key: value` is an object entry. A `key:` line with an indented block under it is
  a nested object. `key: {}` is an empty object. Indentation is spaces.
- `key[N]: a,b,c` is an array of N scalars.
- `key[N]{f1,f2}:` followed by N indented comma-separated rows is an array of N
  objects; each row's cells map to the fields f1,f2 in order.
- `key[N]:` followed by N `- item` lines is a mixed array. `-` alone introduces an
  object element (indented block); `- [N]: ...` a nested array; `- {}` an empty object.
- Values are strings unless they are exactly `null`, `true`, `false`, or a JSON
  number. Double-quoted values are JSON strings (with escapes); quoting is used when
  a bare value would be misread (numbers-as-strings, values containing the
  delimiter, leading/trailing spaces, empty strings).
- `[N]` counts are exact. When emitting HAAL, count your rows and make N match.
- Full-line `#` lines are comments.

Example:
users[2]{id,name,active}:
 1,Ada Lovelace,true
 2,Grace Hopper,false
means: {"users":[{"id":1,"name":"Ada Lovelace","active":true},
{"id":2,"name":"Grace Hopper","active":false}]}
```

---

## Notes

- For **reading only** (you serialize, the model consumes), many models handle the
  tabular form without any primer — it resembles CSV and markdown tables. Keep the
  block anyway for reliability on nested forms; it is cheap.
- For **writing** (the model emits HAAL you will parse), always include the block,
  always validate with `haaland.loads()`, and feed decode errors back on retry —
  see [../docs/llm-integration.md](../docs/llm-integration.md).
- Measure the block's token cost yourself: `haal stats` or your provider's token
  counter. The 344-token figure is measured with tiktoken `o200k_base` on the block between
  the fences above; re-measure if you edit it.
