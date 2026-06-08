"""Model tier selection and escalation."""

from __future__ import annotations

import config


def select_model(state: dict) -> str:
    if state["baseline"]:
        return config.MODEL_LARGE
    if state["test_failures"] >= 2:
        return config.MODEL_LARGE
    if len(state["files_touched"]) > config.ROUTER_FILE_THRESHOLD:
        return config.MODEL_LARGE
    return config.MODEL_SMALL
