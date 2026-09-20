"""Configuration loading for the standalone graphskillevo method."""
from __future__ import annotations

import copy
import datetime
import os
from dataclasses import asdict, dataclass
from typing import Any

from graphskillevo.base_config import apply_overrides, flatten_config, is_structured, load_config


@dataclass(slots=True)
class EvolutionConfig:
    population_size: int = 6
    generations: int = 3
    train_eval_num: int = 0
    reflection_failure_k: int = 3
    include_hidden_reference: bool = True
    operator_max_completion_tokens: int = 64000
    operator_reasoning_effort: str = "medium"
    initial_include_base_skill: bool = True
    graph_retry_attempts: int = 3


_OPENAI_DEFAULT_MODEL_SENTINELS = {"gpt-5.4", "gpt-5.5"}
_BACKEND_ALIASES = {
    "azure": "azure_openai",
    "azure_openai": "azure_openai",
    "azure-openai": "azure_openai",
    "openai_chat": "openai_chat",
    "openai": "openai_chat",
    "codex": "codex_exec",
    "codex_exec": "codex_exec",
}
_BACKEND_DEFAULT_MODELS = {
    "azure_openai": "gpt-4o",
    "openai_chat": "gpt-4o",
    "codex_exec": "gpt-4o",
}

_SKILLS_TREE_ENV_DIRS = {
    "alfworld": "alfworld",
    "docvqa": "docvqa",
    "searchqa": "searchqa",
    "spreadsheetbench": "spreadsheetbench",
    "livemathematicianbench": "livemathematicianbench",
}


def normalize_backend_name(name: str | None) -> str:
    normalized = str(name or "").strip().lower()
    return _BACKEND_ALIASES.get(normalized, normalized or "azure_openai")


def default_model_for_backend(backend: str | None) -> str:
    return _BACKEND_DEFAULT_MODELS.get(
        normalize_backend_name(backend),
        _BACKEND_DEFAULT_MODELS["azure_openai"],
    )


def graph_skill_init_path(env_name: str | None) -> str:
    """Return the default graph-structured initial skill path for an environment."""
    env_key = str(env_name or "").strip().lower()
    tree_dir = _SKILLS_TREE_ENV_DIRS.get(env_key)
    if tree_dir is None:
        raise ValueError(
            f"No graph initial skill mapping for environment {env_name!r}. "
            f"Available: {sorted(_SKILLS_TREE_ENV_DIRS)}"
        )
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(
        project_root,
        "graphskillevo",
        "initial_skills",
        tree_dir,
        "init_skill.md",
    )
    if not os.path.isfile(path):
        raise ValueError(f"Graph initial skill does not exist: {path}")
    return os.path.abspath(path)


def _has_explicit_skill_init(
    *,
    cfg_options: list[str] | None,
    legacy_overrides: dict[str, Any] | None,
) -> bool:
    for item in cfg_options or []:
        key, _, _ = str(item).partition("=")
        if key in {"skill_init", "env.skill_init"}:
            return True
    return bool(legacy_overrides and legacy_overrides.get("skill_init") is not None)


def _deep_get(cfg: dict, dotted: str, default: Any = None) -> Any:
    cur: Any = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _deep_set(cfg: dict, dotted: str, value: Any) -> None:
    cur = cfg
    parts = dotted.split(".")
    for part in parts[:-1]:
        node = cur.get(part)
        if not isinstance(node, dict):
            node = {}
            cur[part] = node
        cur = node
    cur[parts[-1]] = value


def _cast_value(text: str) -> Any:
    raw = str(text)
    lowered = raw.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def _apply_mixed_overrides(cfg: dict, overrides: list[str]) -> None:
    evolution_overrides: list[tuple[str, Any]] = []
    base_overrides: list[str] = []
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid override (expected key=value): {item!r}")
        key, raw_value = item.split("=", 1)
        if key.startswith("graphskillevo."):
            evolution_overrides.append((key.removeprefix("graphskillevo."), _cast_value(raw_value)))
        elif key.startswith("evolution."):
            evolution_overrides.append((key.removeprefix("evolution."), _cast_value(raw_value)))
        else:
            base_overrides.append(item)

    if base_overrides:
        apply_overrides(cfg, base_overrides)
    if evolution_overrides:
        cfg.setdefault("graphskillevo", {})
    for key, value in evolution_overrides:
        _deep_set(cfg, f"graphskillevo.{key}", value)


def _legacy_to_structured(key: str) -> str:
    mapping = {
        "backend": "model.backend",
        "optimizer_model": "model.optimizer",
        "target_model": "model.target",
        "optimizer_backend": "model.optimizer_backend",
        "target_backend": "model.target_backend",
        "reasoning_effort": "model.reasoning_effort",
        "skill_init": "env.skill_init",
        "out_root": "env.out_root",
        "env": "env.name",
        "batch_size": "train.batch_size",
        "train_size": "train.train_size",
        "seed": "train.seed",
    }
    return mapping.get(key, f"env.{key}")


def _finalize_backend_defaults(flat: dict, *, explicit_backend: str | None = None) -> None:
    backend = normalize_backend_name(flat.get("model_backend") or flat.get("target_backend") or "azure_openai")
    if explicit_backend is not None:
        backend = normalize_backend_name(explicit_backend)
        flat["model_backend"] = backend
        if backend == "codex_exec":
            flat.setdefault("optimizer_backend", "openai_chat")
            flat.setdefault("target_backend", "codex_exec")
        else:
            flat.setdefault("optimizer_backend", "openai_chat")
            flat.setdefault("target_backend", "openai_chat")
    else:
        flat.setdefault("optimizer_backend", "openai_chat")
        flat.setdefault("target_backend", "openai_chat")

    if flat.get("optimizer_backend") != "openai_chat":
        raise ValueError("optimizer_backend must be openai_chat")
    if flat.get("target_backend") not in {"openai_chat", "codex_exec"}:
        raise ValueError("target_backend must be openai_chat or codex_exec")


def _parse_evolution_config(raw: dict) -> EvolutionConfig:
    removed = {"selection_mode", "val_eval_num"}.intersection(raw or {})
    if removed:
        names = ", ".join(f"graphskillevo.{name}" for name in sorted(removed))
        raise ValueError(f"{names} is no longer supported; graphskillevo always selects on full valid_seen")
    data = asdict(EvolutionConfig())
    data.update(raw or {})
    evolution = EvolutionConfig(**{key: data[key] for key in data if key in EvolutionConfig.__dataclass_fields__})
    evolution.population_size = int(evolution.population_size)
    evolution.generations = int(evolution.generations)
    evolution.train_eval_num = int(evolution.train_eval_num)
    evolution.reflection_failure_k = int(evolution.reflection_failure_k)
    evolution.include_hidden_reference = _as_bool(evolution.include_hidden_reference)
    evolution.operator_max_completion_tokens = int(evolution.operator_max_completion_tokens)
    evolution.initial_include_base_skill = _as_bool(evolution.initial_include_base_skill)
    evolution.graph_retry_attempts = int(evolution.graph_retry_attempts)
    if evolution.population_size <= 0:
        raise ValueError(f"population_size must be positive, got {evolution.population_size}")
    if evolution.generations < 0:
        raise ValueError(f"generations must be >= 0, got {evolution.generations}")
    if evolution.reflection_failure_k < 0:
        raise ValueError(f"reflection_failure_k must be >= 0, got {evolution.reflection_failure_k}")
    if evolution.graph_retry_attempts <= 0:
        raise ValueError(f"graph_retry_attempts must be positive, got {evolution.graph_retry_attempts}")
    return evolution


def load_graphskillevo_config(
    config_path: str,
    *,
    cfg_options: list[str] | None = None,
    legacy_overrides: dict[str, Any] | None = None,
    evolution_overrides: dict[str, Any] | None = None,
) -> tuple[dict, EvolutionConfig]:
    """Load a GraphSkillEvo config plus method-specific evolution settings."""
    cfg = load_config(config_path)
    cfg = copy.deepcopy(cfg)
    structured = is_structured(cfg)
    explicit_skill_init = _has_explicit_skill_init(
        cfg_options=cfg_options,
        legacy_overrides=legacy_overrides,
    )

    explicit_backend: str | None = None
    for option in cfg_options or []:
        key, _, raw_value = str(option).partition("=")
        if key == "model.backend":
            explicit_backend = raw_value
            break

    if cfg_options:
        _apply_mixed_overrides(cfg, cfg_options)

    if legacy_overrides:
        mapped: list[str] = []
        for key, value in legacy_overrides.items():
            if value is None:
                continue
            if key == "backend":
                explicit_backend = str(value)
            dotted = _legacy_to_structured(key) if structured else key
            mapped.append(f"{dotted}={value}")
        if mapped:
            _apply_mixed_overrides(cfg, mapped)

    if evolution_overrides:
        cfg.setdefault("graphskillevo", {})
        for key, value in evolution_overrides.items():
            _deep_set(cfg, f"graphskillevo.{key}", value)

    evolution = _parse_evolution_config(_deep_get(cfg, "graphskillevo", {}))
    flat = (
        flatten_config(cfg)
        if structured
        else {key: value for key, value in cfg.items() if key not in {"graphskillevo", "evolution"}}
    )

    for new_key, old_key in (
        ("azure_openai_endpoint", "azure_endpoint"),
        ("azure_openai_api_version", "azure_api_version"),
        ("azure_openai_api_key", "azure_api_key"),
    ):
        if flat.get(new_key) in (None, "") and flat.get(old_key) not in (None, ""):
            flat[new_key] = flat[old_key]

    _finalize_backend_defaults(flat, explicit_backend=explicit_backend)
    flat.setdefault("seed", 42)
    flat.setdefault("optimizer_model", default_model_for_backend(flat.get("optimizer_backend")))
    flat.setdefault("target_model", default_model_for_backend(flat.get("target_backend")))
    if not explicit_skill_init:
        flat["skill_init"] = graph_skill_init_path(flat.get("env"))

    if not flat.get("out_root"):
        env = flat.get("env", "unknown")
        model = str(flat.get("optimizer_model", "unknown")).replace("/", "-")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        flat["out_root"] = os.path.join("outputs", f"graphskillevo_{env}_{model}_{ts}")
    flat["out_root"] = os.path.abspath(str(flat["out_root"]))

    if not evolution.operator_reasoning_effort:
        evolution.operator_reasoning_effort = str(flat.get("reasoning_effort") or "")

    return flat, evolution
