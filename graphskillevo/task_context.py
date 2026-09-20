"""Task context prompt loading for graph-skill initialization."""
from __future__ import annotations

from typing import Any

from graphskillevo.prompts import load_prompt

_TASK_CONTEXT_PROMPTS = {
    "alfworld": ("alfworld", "task_context_alfworld"),
    "docvqa": ("docvqa", "task_context_docvqa"),
    "livemath": ("livemathematicianbench", "task_context_livemathematicianbench"),
    "livemathematicianbench": (
        "livemathematicianbench",
        "task_context_livemathematicianbench",
    ),
    "searchqa": ("searchqa", "task_context_searchqa"),
    "spreadsheetbench": ("spreadsheetbench", "task_context_spreadsheetbench"),
}


def build_initial_task_context(cfg: dict[str, Any]) -> str:
    """Return the environment-specific task context prompt for initialization."""
    env_name = str(cfg.get("env", "") or "").strip()
    env_key = env_name.lower()
    prompt_spec = _TASK_CONTEXT_PROMPTS.get(env_key)
    if prompt_spec:
        prompt_env, prompt_name = prompt_spec
        try:
            context = load_prompt(prompt_name, env=prompt_env).strip()
        except FileNotFoundError:
            context = ""
        if context:
            return context

    return f"Environment name: {env_name}".rstrip()
