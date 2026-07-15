# HAAL by example

Every construct in the format, JSON on the left, HAAL on the right. The formal rules
live in [spec.md](spec.md); this page is the fast tour.

## Scalars and objects

```json
{"name": "gateway", "port": 8443, "tls": true, "notes": null}
```

```
name: gateway
port: 8443
tls: true
notes: null
```

One line per entry. No quotes or braces. Nesting is indentation (1 space per level):

```json
{"server": {"listen": {"host": "0.0.0.0", "port": 8443}}}
```

```
server:
 listen:
  host: 0.0.0.0
  port: 8443
```

## Strings — bare by default, quoted only when needed

```
title: hello world             ← spaces are fine; value runs to end of line
path: /var/log/app.log
note: contains: colons, commas ← fine in value position
count: "42"                    ← string that looks like a number: quoted
flag: "true"                   ← string that looks like a keyword: quoted
empty: ""
multi: "line one\nline two"    ← control characters: JSON escapes
```

A bare token decodes as a number/boolean/null only if it matches those grammars
exactly — everything else is a verbatim string. The encoder adds quotes precisely
when a bare rendering would be misread, so round-trips are exact.

## Arrays of scalars — inline

```json
{"tags": ["infra", "urgent", "p0"], "empty": []}
```

```
tags[3]: infra,urgent,p0
empty[0]:
```

The `[N]` is a declared length, validated at parse time.

## Arrays of uniform objects — tabular (the big win)

```json
{"users": [
  {"id": 1, "name": "Ada Lovelace", "role": "admin"},
  {"id": 2, "name": "Grace Hopper", "role": "editor"}
]}
```

```
users[2]{id,name,role}:
 1,Ada Lovelace,admin
 2,Grace Hopper,editor
```

Applies when every element has the same keys in the same order with scalar values.
Keys are paid for once instead of once per element — this is where the measured
30–40% savings on record-shaped data comes from.

Cells containing the delimiter are quoted:

```
products[2]{sku,desc}:
 A1,"cable, usb-c"
 B2,plain desc
```

## Mixed arrays — list form

```json
{"mixed": [42, "text", {"a": 1}, [1, 2], {}]}
```

```
mixed[5]:
 - 42
 - text
 -
  a: 1
 - [2]: 1,2
 - {}
```

`-` alone introduces an object element as an indented block; `- [N]...` nests an
array; `- {}` is the empty object.

## Root values

Any JSON value can be a document:

```
[3]: 1,2,3          ← root array
[2]{a,b}:           ← root table
 1,2
 3,4
{}                  ← root empty object
42                  ← root scalar
```

## Comments and blank lines

Full-line `#` comments and blank lines are ignored by the decoder (the encoder never
emits them — strings that could be mistaken for them are quoted):

```
# nightly export, 2026-07-14
users[1]{id,name}:
 1,Ada
```

## Validation you get for free

The decoder rejects — with line numbers:

- `users[3]{...}` followed by 2 rows (truncation) or 4 rows (drift)
- rows whose cell count doesn't match the header
- duplicate keys or fields
- empty cells (`1,,2` — an empty string is always `""`)
- tabs in indentation, inconsistent sibling indentation, trailing garbage

This is deliberate: when an LLM emits HAAL, structural damage becomes a caught
exception instead of silently wrong data.
