# Enterprise adoption guide

For teams evaluating HAAL at organizational scale: cost modeling, rollout strategy,
and risk assessment.

## Cost model

Token savings translate to spend linearly on the input side. The formula:

```
monthly_savings = monthly_input_tokens_on_serialized_data
                × haal_savings_rate_for_your_payload_shape
                × price_per_input_token
```

Two of the three factors are **yours to measure** — do not use our averages:

1. `monthly_input_tokens_on_serialized_data`: from your API usage dashboards. In
   RAG/agent/analytics workloads, serialized records are commonly the majority of
   input tokens; measure, don't assume.
2. `haal_savings_rate`: run `haal stats` (OpenAI tokenizers) or
   `benchmarks/run_anthropic.py` (Anthropic, needs your API key) on samples of your
   actual payloads. Our measured range across dataset shapes is **−13.6% (worse) to
   +37.4% (better)** vs. compact JSON — payload shape dominates.

### Worked illustration

The arithmetic below uses our *measured* per-shape savings and Anthropic's published
per-token prices (verified 2026-07: Claude Opus 4.8 $5.00 per million input tokens;
Claude Sonnet 5 $3.00/MTok; Claude Haiku 4.5 $1.00/MTok). **Caveat:** the savings
rates were measured under OpenAI's public `o200k_base` vocabulary because Anthropic's
tokenizer is not runnable offline; your Claude percentages will differ — measure with
`benchmarks/run_anthropic.py` before budgeting.

A workload pushing **2 billion input tokens/month** of event-log-shaped data
(our measured −37.4% shape) through Claude Opus 4.8 at $5.00/MTok:

- JSON baseline: 2,000 MTok × $5.00 = $10,000/month
- HAAL (if the −37.4% rate held on Claude's tokenizer): ≈ $6,260/month
- Illustrative saving: ≈ $3,740/month, before prompt-caching interactions

The same math at Haiku 4.5 prices ($1.00/MTok) yields ≈ $748/month — token
efficiency matters most on premium models and high volumes.

### Interactions to model

- **Prompt caching** (all major providers): cached input re-reads are billed at a
  small fraction of base price. HAAL still helps — smaller payloads mean smaller
  cache writes and more usable context — but compute savings on the *uncached* and
  *cache-write* portions, not gross tokens.
- **Batch APIs** bill at ~50% of standard price; savings halve accordingly.
- **Context-window headroom** is often worth more than the dollars: −37% on tool
  results is +59% more records per context at the same budget.
- **Latency**: input tokens also cost prefill time. Fewer tokens in ⇒ lower
  time-to-first-token, though the effect varies by provider and load.

## Rollout strategy

Phase the adoption; each phase is independently reversible.

**Phase 0 — Measure (days).** Sample real payloads from your prompt-assembly layer.
Run `haal stats` on each class. Output: a table of payload classes with measured
savings. Kill criterion: nothing clears 10%.

**Phase 1 — Read-only pilot (1–2 weeks).** Convert *input* serialization on one
high-volume, low-risk path (tool results or RAG metadata are ideal). Keep model
outputs untouched. A/B task quality on your eval set (see
[llm-integration.md](llm-integration.md#evaluating-comprehension)). Track: task
accuracy delta, realized token/spend delta.

**Phase 2 — Fleet input conversion.** Roll the shim pattern
([prompts/agent-setup.md](../prompts/agent-setup.md#for-platforminfra-teams)) into
your prompt-assembly library so the HAAL-vs-JSON choice is empirical per payload
class, centrally controlled, and instantly revertible via config.

**Phase 3 — LLM-emitted HAAL (optional).** Only for bulk extraction paths, only
with the validation-retry loop, and never in place of provider-enforced structured
outputs.

## Risk assessment

| Risk | Assessment | Mitigation |
|---|---|---|
| Data corruption in transit | Codec is lossless by construction; `loads(dumps(x)) == x` property-tested (25k+ random documents in CI) | Keep round-trip asserts in your pipeline tests |
| Model misreads HAAL | Real but task-dependent; tabular form resembles CSV | Phase 1 A/B gate; keep JSON fallback flag |
| Truncated LLM output parsed as valid | Lower than JSON: `[N]` markers make truncation a hard error | Always parse with strict `haaland.loads` |
| Format lock-in | Low: HAAL⇄JSON conversion is total and cheap (`haal decode`) | Store at rest as JSON; convert at the prompt boundary |
| Spec churn | Pre-1.0; syntax changes will be major-versioned | Pin the package version; the v0.1 syntax is stable |
| Supply chain | Zero runtime dependencies; 560-line core codec, auditable in an afternoon | Vendor the two source files if policy requires |

## Security and compliance notes

- HAAL is a *representation*, not a transport or crypto layer; it inherits your
  existing controls. Payloads remain plain text — DLP/redaction tooling that scans
  prompt text keeps working.
- The decoder is strict and non-recursive-descent-hostile: no code execution, no
  references/anchors (unlike YAML), no billion-laughs-style expansion vectors, and
  documents are size-bounded by your own inputs.
- License: MIT. No telemetry, no network calls anywhere in the package.

## Support expectations

This is an open-source project, not a commercial product. File issues on GitHub;
security reports per [SECURITY.md](../SECURITY.md). For mission-critical use, the
codebase is small enough to fork and own — that is a feature.
