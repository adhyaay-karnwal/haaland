# HAAL Format Specification

**Version:** 0.1 (draft)
**Status:** Stable syntax; open to extension before 1.0.

HAAL (the *Haaland* serialization language) is a plain-text encoding of the JSON data
model, designed to minimize the number of tokens a byte-pair-encoding (BPE) tokenizer
produces for the same information. It is line-oriented, indentation-structured, and
self-validating.

## 1. Design goals

1. **Token efficiency.** Every rule exists to remove characters that BPE tokenizers bill
   as separate tokens: repeated object keys, quotes, braces, and commas.
2. **Losslessness.** `decode(encode(x)) == x` for every value in the JSON data model,
   including object key order. HAAL is a *representation* of JSON, not a new data model.
3. **Verifiability.** Arrays declare their length (`[N]`) and tables declare their
   fields, so a consumer — human, program, or LLM — can detect truncation and drift.
4. **Determinism.** For a given value and codec options, there is exactly one canonical
   encoding.

## 2. Data model

HAAL represents exactly the JSON data model:

- `null`, booleans, numbers (finite IEEE-754 doubles and arbitrary-precision integers),
  strings, arrays, and objects with string keys.
- `NaN` and `Infinity` are not representable (as in strict JSON).
- Object key order is significant and preserved.
- Duplicate keys are an error.

## 3. Lexical structure

- Documents are UTF-8 text. Lines are separated by `\n`; a trailing `\r` on any line is
  ignored (CRLF input is accepted).
- **Indentation** carries structure and consists of spaces only. Tabs in indentation are
  an error. The canonical encoder emits **1 space per level** (the measured optimum —
  see `benchmarks/`); decoders accept any consistent per-block width.
- Blank lines and lines whose first non-space character is `#` (comments) are ignored.
  The encoder never emits either; data that could be mistaken for them is quoted.
- The **delimiter** separates cells in rows and inline arrays. Canonical: `,`.
  Supported: `,`, tab, `|`, `;`. Encoder and decoder must agree on the delimiter (it is
  a codec parameter, not sniffed).

## 4. Scalars

| Value | Encoding |
|---|---|
| `null` | `null` |
| `true` / `false` | `true` / `false` |
| number | shortest decimal form; JSON number grammar |
| string (safe) | written bare, verbatim |
| string (unsafe) | JSON string literal (`"..."` with JSON escapes) |

A bare token decodes as `null`/`true`/`false` if it equals one of those keywords, as a
number if it matches the JSON number grammar exactly (so `007` and `+1` remain strings),
otherwise as a verbatim string.

A string **must be quoted** when it would otherwise be misread. In every context:

- it is empty, or has leading/trailing whitespace,
- it contains a control character (U+0000–U+001F, U+007F) — this includes newlines,
- it begins with `"`,
- it equals `null`, `true`, or `false`, or matches the JSON number grammar.

Additional rules per context:

| Context | Extra quoting condition |
|---|---|
| **line** — after `key: `, runs to end of line | equals `{}` |
| **cell** — element of a row or inline array | contains the delimiter, or begins with `#` |
| **list** — after `- ` | begins with `[`, or equals `{}` |
| **root** — a single-line scalar document | anything not matching `[A-Za-z0-9_][A-Za-z0-9_./+-]*` |

## 5. Objects

Each entry is one line at the object's indentation level:

```
key: scalar
nested:
 inner: 1
empty: {}
```

- `key: <scalar>` — scalar value (the value runs to end of line).
- `key:` with nothing after — a non-empty object block, indented one level deeper.
- `key: {}` — the empty object.
- Array values attach an array header to the key (§6).

**Keys** are written bare when they match `[A-Za-z0-9_][A-Za-z0-9_./+-]*`; otherwise
they are JSON string literals. This character set can never collide with structure
(`:`, `[`, `{`, `"`, `#`, whitespace, or any supported delimiter).

## 6. Arrays

Every array declares its length `N`. Three forms, chosen deterministically:

### 6.1 Inline (all elements are scalars)

```
tags[3]: alpha,beta,gamma
empty[0]:
```

Cells use **cell** context quoting. `[0]:` is the empty array.

### 6.2 Tabular (uniform arrays of flat objects)

Used when the array is non-empty and every element is a non-empty object with the
**same keys in the same order**, all of whose values are scalars:

```
users[3]{id,name,active}:
 1,Ada,true
 2,Grace,false
 3,Linus,true
```

The header names each field once; each element becomes one row of cells. Field names
follow key quoting rules. Exactly `N` rows must follow, each with exactly as many cells
as fields. This form is where HAAL's token savings concentrate: JSON repeats every key
for every element; HAAL writes each key once.

### 6.3 List (everything else)

```
mixed[4]:
 - 42
 - plain text
 -
  name: nested object
 - [2]: 1,2
```

Each element is one item at one level deeper:

- `- <scalar>` — scalar element (**list** context quoting; rest of line).
- `-` alone — a non-empty object element, as a block one level deeper.
- `- {}` — the empty object.
- `- [N]...` — a nested array (any of the three forms, anchored at the item line).

### 6.4 Root arrays

A document whose value is an array starts with the header at column 0, without a key:
`[3]: 1,2,3`, or `[N]{...}:` with rows, or `[N]:` with list items.

## 7. Documents

A document encodes exactly one value:

- **Object** — non-empty: its entries at indentation 0; empty: the single line `{}`.
- **Array** — a root array header (§6.4).
- **Scalar** — a single line (**root** context quoting).

An empty (or all-blank/comment) document is an error. Content after the encoded value
is an error.

## 8. Validation semantics

Decoders MUST reject:

- length mismatches (`[N]` vs. actual cells, rows, or items — both too few and too many),
- row width mismatches against the field header,
- duplicate object keys and duplicate field names,
- tabs in indentation and inconsistent sibling indentation,
- empty cells (`1,,2`) — an empty string is always `""`,
- unterminated quoted strings, malformed headers, and trailing content.

These checks are the reason `[N]{fields}` exists: when an LLM *emits* HAAL, the declared
length and field list make truncated or hallucinated structure detectable at parse time.

## 9. Conformance

An implementation is conforming if:

1. `decode(encode(x))` equals `x` (including key order) for every JSON-model value `x`;
2. it produces the canonical encoding (this spec) for every value under default options;
3. it rejects every document invalid under §8.

The reference implementation (`src/haaland/`) plus the test suite (`tests/`, including
property-based round-trip tests) define behavior where this document is ambiguous.

## 10. Media type and file extension

- File extension: `.haal`
- Suggested media type (unregistered): `text/x-haal; charset=utf-8`

## 11. Versioning

The format follows the library's semantic version. Documents do not carry a version
marker (markers cost tokens); any future syntax change that is not backward-compatible
will be a major version and use a distinct file extension.
