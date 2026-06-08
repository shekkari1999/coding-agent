import config
from agent.router import select_model


def _state(**kwargs):
    base = {
        "baseline": False,
        "test_failures": 0,
        "files_touched": [],
    }
    base.update(kwargs)
    return base


def test_baseline_uses_large_model():
    assert select_model(_state(baseline=True)) == config.MODEL_LARGE


def test_escalates_after_test_failures():
    assert select_model(_state(test_failures=2)) == config.MODEL_LARGE


def test_small_model_by_default():
    assert select_model(_state()) == config.MODEL_SMALL
