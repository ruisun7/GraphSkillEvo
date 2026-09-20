"""Small utilities for graphskillevo."""
from __future__ import annotations

import json
import os
from typing import Any


SECRET_KEYS = {
    "azure_api_key",
    "api_key",
    "openai_api_key",
    "azure_openai_api_key",
    "optimizer_azure_openai_api_key",
    "target_azure_openai_api_key",
}


def redact_cfg(cfg: dict) -> dict:
    redacted = dict(cfg)
    for key in list(redacted):
        value = redacted.get(key)
        if key.lower() in SECRET_KEYS and value:
            text = str(value)
            redacted[key] = "*" * len(text) if len(text) <= 8 else f"{text[:4]}...{text[-4:]}"
    return redacted


def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_text_if_exists(path: str) -> str:
    if not path or not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def token_delta(before: dict, after: dict) -> dict:
    out: dict = {}
    for stage, values in after.items():
        if stage == "_total":
            continue
        prev = before.get(stage, {})
        out[stage] = {
            "calls": values.get("calls", 0) - prev.get("calls", 0),
            "prompt_tokens": values.get("prompt_tokens", 0) - prev.get("prompt_tokens", 0),
            "completion_tokens": values.get("completion_tokens", 0) - prev.get("completion_tokens", 0),
        }
    return out
