"""Scrape vLLM Prometheus metrics and compute per-task deltas."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

import config

METRIC_NAMES = (
    "vllm:prefix_cache_hits",
    "vllm:prefix_cache_queries",
    "vllm:prompt_tokens_total",
    "vllm:generation_tokens_total",
)

GAUGE_NAMES = (
    "vllm:gpu_prefix_cache_hit_rate",
    "vllm:cpu_prefix_cache_hit_rate",
)


@dataclass
class MetricsSnapshot:
    counters: dict[str, float]
    gauges: dict[str, float]

    @classmethod
    def empty(cls) -> MetricsSnapshot:
        return cls(counters={}, gauges={})


@dataclass
class TaskMetrics:
    prompt_tokens: int
    generation_tokens: int
    cache_hits: int
    cache_queries: int
    cache_hit_rate: float | None
    duration_s: float
    cost_usd: float
    prefill_price_per_1m: float
    decode_price_per_1m: float
    available: bool


def metrics_url() -> str:
    explicit = config.VLLM_METRICS_URL
    if explicit:
        return explicit
    base = config.VLLM_BASE_URL.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    return f"{base}/metrics"


def capture_metrics() -> MetricsSnapshot:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(metrics_url())
            resp.raise_for_status()
            return parse_prometheus(resp.text)
    except (httpx.HTTPError, OSError):
        return MetricsSnapshot.empty()


def compute_token_cost(prompt_tokens: int, generation_tokens: int) -> float:
    prefill_rate = config.prefill_price_per_1m()
    decode_rate = config.decode_price_per_1m()
    return (
        prompt_tokens * prefill_rate / 1_000_000
        + generation_tokens * decode_rate / 1_000_000
    )


def compute_deltas(
    before: MetricsSnapshot,
    after: MetricsSnapshot,
    duration_s: float = 0.0,
) -> TaskMetrics:
    prompt = _counter_delta(before, after, "vllm:prompt_tokens_total")
    generation = _counter_delta(before, after, "vllm:generation_tokens_total")
    hits = _counter_delta(before, after, "vllm:prefix_cache_hits")
    queries = _counter_delta(before, after, "vllm:prefix_cache_queries")

    hit_rate = None
    if queries > 0:
        hit_rate = hits / queries
    else:
        for name in GAUGE_NAMES:
            if name in after.gauges:
                hit_rate = after.gauges[name]
                break

    prefill_rate = config.prefill_price_per_1m()
    decode_rate = config.decode_price_per_1m()
    cost = compute_token_cost(prompt, generation)

    available = any(
        name in before.counters or name in after.counters for name in METRIC_NAMES
    )

    return TaskMetrics(
        prompt_tokens=prompt,
        generation_tokens=generation,
        cache_hits=hits,
        cache_queries=queries,
        cache_hit_rate=hit_rate,
        duration_s=duration_s,
        cost_usd=cost,
        prefill_price_per_1m=prefill_rate,
        decode_price_per_1m=decode_rate,
        available=available,
    )


def format_metrics_block(metrics: TaskMetrics) -> str:
    if not metrics.available:
        return "Metrics: unavailable (could not reach vLLM /metrics)"

    lines = [
        "Metrics:",
        f"  Tokens:     {metrics.prompt_tokens:,} prompt / {metrics.generation_tokens:,} generated",
        f"  Duration:   {metrics.duration_s:.1f}s",
        f"  Cost:       ${metrics.cost_usd:.4f}",
        f"              (${metrics.prefill_price_per_1m:.2f}/M prefill, ${metrics.decode_price_per_1m:.2f}/M decode)",
    ]

    if metrics.cache_hit_rate is not None:
        lines.append(f"  KV cache:   {metrics.cache_hit_rate * 100:.1f}% hit rate")
    elif metrics.cache_queries > 0:
        lines.append(f"  KV cache:   {metrics.cache_hits:,} hits / {metrics.cache_queries:,} queries")

    return "\n".join(lines)


def parse_prometheus(text: str) -> MetricsSnapshot:
    counters: dict[str, float] = {}
    gauges: dict[str, float] = {}

    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([a-zA-Z0-9_:]+)(?:\{[^}]*\})?\s+([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)$", line)
        if not match:
            continue
        name, raw = match.group(1), float(match.group(2))
        if name in METRIC_NAMES:
            counters[name] = counters.get(name, 0.0) + raw
        elif name in GAUGE_NAMES:
            gauges[name] = raw

    return MetricsSnapshot(counters=counters, gauges=gauges)


def _counter_delta(before: MetricsSnapshot, after: MetricsSnapshot, name: str) -> int:
    start = before.counters.get(name, 0.0)
    end = after.counters.get(name, 0.0)
    return max(0, int(end - start))
