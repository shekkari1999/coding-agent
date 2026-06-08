from agent.metrics import MetricsSnapshot, compute_deltas, parse_prometheus


SAMPLE = """
# HELP vllm:prompt_tokens_total Total prompt tokens
# TYPE vllm:prompt_tokens_total counter
vllm:prompt_tokens_total{model="Qwen/Qwen2.5-7B-Instruct"} 1000.0
vllm:generation_tokens_total{model="Qwen/Qwen2.5-7B-Instruct"} 50.0
vllm:prefix_cache_hits{model="Qwen/Qwen2.5-7B-Instruct"} 10.0
vllm:prefix_cache_queries{model="Qwen/Qwen2.5-7B-Instruct"} 40.0
vllm:gpu_prefix_cache_hit_rate 0.25
"""


def test_parse_prometheus():
    snap = parse_prometheus(SAMPLE)
    assert snap.counters["vllm:prompt_tokens_total"] == 1000.0
    assert snap.gauges["vllm:gpu_prefix_cache_hit_rate"] == 0.25


def test_compute_deltas():
    before = parse_prometheus(SAMPLE)
    after_text = SAMPLE.replace("1000.0", "1500.0").replace("50.0", "80.0")
    after_text = after_text.replace("10.0", "25.0").replace("40.0", "60.0")
    after = parse_prometheus(after_text)

    metrics = compute_deltas(before, after, duration_s=10.0)
    assert metrics.prompt_tokens == 500
    assert metrics.generation_tokens == 30
    assert metrics.cache_hits == 15
    assert metrics.cache_queries == 20
    assert metrics.cache_hit_rate == 0.75
    assert metrics.duration_s == 10.0
    assert metrics.gpu_cost_usd > 0
