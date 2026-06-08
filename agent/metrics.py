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
    gpu_cost_usd: float
    nominal_cost_usd: float
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

    nominal = (
        prompt * config.PROMPT_PRICE_PER_1M / 1_000_000
        + generation * config.COMPLETION_PRICE_PER_1M / 1_000_000
    )
    gpu_cost = duration_s / 3600 * config.GPU_PRICE_PER_HR

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
        gpu_cost_usd=gpu_cost,
        nominal_cost_usd=nominal,
        available=available,
    )


def format_metrics_block(metrics: TaskMetrics) -> str:
    if not metrics.available:
        return "Metrics: unavailable (could not reach vLLM /metrics)"

    lines = [
        "Metrics:",
        f"  Tokens:     {metrics.prompt_tokens:,} prompt / {metrics.generation_tokens:,} generated",
        f"  Duration:   {metrics.duration_s:.1f}s",
        f"  GPU cost:   ${metrics.gpu_cost_usd:.4f}  (at ${config.GPU_PRICE_PER_HR}/hr)",
    ]

    if metrics.cache_hit_rate is not None:
        lines.append(f"  KV cache:   {metrics.cache_hit_rate * 100:.1f}% hit rate")
    elif metrics.cache_queries > 0:
        lines.append(f"  KV cache:   {metrics.cache_hits:,} hits / {metrics.cache_queries:,} queries")

    if config.PROMPT_PRICE_PER_1M or config.COMPLETION_PRICE_PER_1M:
        lines.append(f"  Token est:  ${metrics.nominal_cost_usd:.4f}  (nominal, for comparison)")

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
