"""Deterministic benchmark datasets.

Every dataset is generated from a fixed seed, so token counts are exactly
reproducible on any machine. The shapes are modeled on common LLM-context
payloads: API results, database rows, event logs, metrics, configuration,
and retrieval chunks.

The suite deliberately includes shapes where HAAL's advantage is small
(deep config, prose-heavy chunks) as well as shapes where it is large
(uniform records), so reported averages are honest.
"""

from __future__ import annotations

import random

_FIRST = [
    "Ada",
    "Grace",
    "Alan",
    "Edsger",
    "Barbara",
    "Donald",
    "Leslie",
    "Tony",
    "John",
    "Margaret",
    "Radia",
    "Vint",
    "Tim",
    "Frances",
    "Ken",
    "Dennis",
    "Bjarne",
    "Guido",
    "Anders",
    "Yukihiro",
    "Brendan",
    "Rich",
    "Martin",
    "Joe",
]
_LAST = [
    "Lovelace",
    "Hopper",
    "Turing",
    "Dijkstra",
    "Liskov",
    "Knuth",
    "Lamport",
    "Hoare",
    "Backus",
    "Hamilton",
    "Perlman",
    "Cerf",
    "Berners-Lee",
    "Allen",
    "Thompson",
    "Ritchie",
    "Stroustrup",
    "Rossum",
    "Hejlsberg",
    "Matsumoto",
]
_DEPTS = ["engineering", "design", "sales", "support", "operations", "finance"]
_CITIES = [
    "Berlin",
    "Oslo",
    "Tokyo",
    "Austin",
    "Toronto",
    "Manchester",
    "Lyon",
    "Seoul",
    "Warsaw",
    "Denver",
    "Osaka",
    "Porto",
]
_PRODUCTS = [
    "usb-c cable",
    "mechanical keyboard",
    "27in monitor",
    "laptop stand",
    "webcam",
    "desk mat",
    "hdmi adapter",
    "wireless mouse",
    "headset",
    "docking station",
    "ergonomic chair",
    "standing desk",
]
_EVENT_TYPES = ["push", "pull_request", "issue_comment", "release", "fork", "star"]
_REPOS = [
    "core/api",
    "core/web",
    "infra/deploy",
    "ml/training",
    "docs/site",
    "tools/cli",
    "core/auth",
    "data/pipeline",
]
_WORDS = [
    "the",
    "model",
    "processes",
    "context",
    "tokens",
    "sequentially",
    "and",
    "attention",
    "cost",
    "grows",
    "with",
    "input",
    "length",
    "so",
    "reducing",
    "serialized",
    "structure",
    "size",
    "directly",
    "lowers",
    "latency",
    "and",
    "spend",
    "for",
    "production",
    "systems",
    "that",
    "pass",
    "records",
    "tables",
    "logs",
    "and",
    "configuration",
    "into",
    "prompts",
    "every",
    "request",
]


def employees(n: int = 100) -> dict:
    """Uniform flat records: the classic rows-into-context payload."""
    rng = random.Random(42)
    rows = []
    for i in range(1, n + 1):
        first = rng.choice(_FIRST)
        last = rng.choice(_LAST)
        y, m, d = rng.randrange(15, 26), rng.randrange(1, 13), rng.randrange(1, 29)
        rows.append(
            {
                "id": i,
                "name": f"{first} {last}",
                "email": f"{first.lower()}.{last.lower()}@example.com",
                "department": rng.choice(_DEPTS),
                "city": rng.choice(_CITIES),
                "salary": rng.randrange(48, 195) * 1000,
                "active": rng.random() < 0.85,
                "joined": f"20{y:02d}-{m:02d}-{d:02d}",
            }
        )
    return {"employees": rows}


def orders(n: int = 50) -> dict:
    """Nested e-commerce orders: objects containing uniform line-item tables."""
    rng = random.Random(7)
    out = []
    for i in range(1, n + 1):
        items = [
            {
                "sku": f"P{rng.randrange(1000, 9999)}",
                "product": rng.choice(_PRODUCTS),
                "qty": rng.randrange(1, 5),
                "unit_price": round(rng.uniform(5, 400), 2),
            }
            for _ in range(rng.randrange(1, 5))
        ]
        out.append(
            {
                "order_id": f"ORD-{100000 + i}",
                "customer": {
                    "name": f"{rng.choice(_FIRST)} {rng.choice(_LAST)}",
                    "city": rng.choice(_CITIES),
                },
                "status": rng.choice(["pending", "shipped", "delivered", "returned"]),
                "items": items,
                "total": round(sum(x["qty"] * x["unit_price"] for x in items), 2),
            }
        )
    return {"orders": out}


def events(n: int = 200) -> dict:
    """API/event-log records, GitHub-webhook shaped."""
    rng = random.Random(1337)
    rows = []
    ts = 1735689600  # 2025-01-01T00:00:00Z
    for i in range(1, n + 1):
        ts += rng.randrange(30, 2000)
        rows.append(
            {
                "id": 9_000_000 + i,
                "type": rng.choice(_EVENT_TYPES),
                "repo": rng.choice(_REPOS),
                "actor": f"{rng.choice(_FIRST).lower()}{rng.randrange(10, 99)}",
                "timestamp": ts,
                "public": rng.random() < 0.9,
            }
        )
    return {"events": rows}


def timeseries(hours: int = 48) -> dict:
    """Numeric metrics: arrays of scalars, one series per metric."""
    rng = random.Random(99)
    base = 1735689600
    return {
        "service": "checkout-api",
        "period": {"start": base, "step_seconds": 3600, "points": hours},
        "metrics": {
            "requests": [rng.randrange(800, 12000) for _ in range(hours)],
            "errors": [rng.randrange(0, 40) for _ in range(hours)],
            "p50_ms": [round(rng.uniform(18, 60), 1) for _ in range(hours)],
            "p99_ms": [round(rng.uniform(90, 900), 1) for _ in range(hours)],
            "cpu_pct": [round(rng.uniform(8, 93), 1) for _ in range(hours)],
        },
    }


def config() -> dict:
    """Deeply nested configuration: few arrays, HAAL's least favorable shape."""
    return {
        "service": {
            "name": "gateway",
            "version": "2.14.0",
            "listen": {"host": "0.0.0.0", "port": 8443, "tls": True},
            "timeouts": {"connect_ms": 500, "read_ms": 3000, "write_ms": 3000},
        },
        "upstreams": {
            "auth": {"url": "http://auth.internal:9000", "retries": 2, "circuit_breaker": True},
            "billing": {
                "url": "http://billing.internal:9001",
                "retries": 3,
                "circuit_breaker": True,
            },
            "search": {
                "url": "http://search.internal:9002",
                "retries": 1,
                "circuit_breaker": False,
            },
        },
        "rate_limits": {
            "anonymous": {"rps": 5, "burst": 20},
            "authenticated": {"rps": 50, "burst": 200},
            "internal": {"rps": 1000, "burst": 2000},
        },
        "features": {
            "request_logging": True,
            "tracing": {"enabled": True, "sample_rate": 0.05},
            "compression": {"enabled": True, "min_bytes": 1024},
        },
        "allowed_origins": [
            "https://app.example.com",
            "https://admin.example.com",
            "https://partner.example.net",
        ],
    }


def chunks(n: int = 30) -> dict:
    """Retrieval chunks: prose-heavy strings with metadata, RAG-shaped.

    Prose dominates the payload, so structural savings are proportionally
    small — included to keep the average honest.
    """
    rng = random.Random(2024)
    rows = []
    for i in range(1, n + 1):
        words = [rng.choice(_WORDS) for _ in range(rng.randrange(25, 60))]
        # Realistic prose contains commas and periods; this matters for
        # delimiter ablations because commas inside cells force quoting.
        for j in range(6, len(words), 7):
            words[j] += ","
        for j in range(11, len(words), 12):
            words[j] = words[j].rstrip(",") + "."
        rows.append(
            {
                "chunk_id": f"doc{rng.randrange(1, 40):02d}#{i:03d}",
                "source": rng.choice(["handbook.pdf", "runbook.md", "api-docs.html", "wiki"]),
                "score": round(rng.uniform(0.62, 0.99), 4),
                "text": " ".join(words),
            }
        )
    return {"chunks": rows}


DATASETS = {
    "employees_100": employees,
    "orders_50": orders,
    "events_200": events,
    "timeseries_48h": timeseries,
    "config": config,
    "rag_chunks_30": chunks,
}
