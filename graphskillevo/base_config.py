"""GraphSkillEvo config loading engine — structured YAML with inheritance.

Supports two config formats:
  1. **Structured** (new): sections like ``model``, ``train``, ``evaluation``,
     ``env`` — with ``_base_`` inheritance.
  2. **Flat** (legacy): all supported keys at top level.

Usage::

    from graphskillevo.config import load_config, flatten_config

    cfg = load_config("configs/searchqa_default.yaml")
    flat = flatten_config(cfg)  # always returns flat dict for trainer
"""
from __future__ import annotations

import copy
import os
from typing import Any

import yaml

# ── Section names that indicate a structured config ──────────────────────

_STRUCTURED_SECTIONS = frozenset({
    "model", "train", "evaluation", "env",
})

_REMOVED_SKILLOPT_SECTIONS = frozenset({"gradient", "optimizer"})
_REMOVED_SKILLOPT_KEYS = frozenset({
    "evaluation.eval_test",
    "evaluation.gate_metric",
    "evaluation.gate_mixed_weight",
    "evaluation.sel_env_num",
    "evaluation.use_gate",
    "model.rewrite_max_completion_tokens",
    "model.rewrite_reasoning_effort",
})
_REMOVED_FLAT_SKILLOPT_KEYS = frozenset({
    "analyst_workers",
    "edit_budget",
    "eval_test",
    "failure_only",
    "gate_metric",
    "gate_mixed_weight",
    "lr_control_mode",
    "lr_scheduler",
    "longitudinal_pair_policy",
    "max_analyst_rounds",
    "merge_batch_size",
    "meta_edit_budget",
    "min_edit_budget",
    "minibatch_size",
    "rewrite_max_completion_tokens",
    "rewrite_reasoning_effort",
    "sel_env_num",
    "skill_update_mode",
    "slow_update_gate_with_selection",
    "slow_update_samples",
    "use_gate",
    "use_meta_skill",
    "use_slow_update",
})

# ── Structured → flat key mapping ────────────────────────────────────────

_FLATTEN_MAP: dict[str, str] = {
    "model.backend": "model_backend",
    "model.optimizer": "optimizer_model",
    "model.target": "target_model",
    "model.optimizer_backend": "optimizer_backend",
    "model.target_backend": "target_backend",
    "model.reasoning_effort": "reasoning_effort",
    "model.codex_exec_path": "codex_exec_path",
    "model.codex_exec_sandbox": "codex_exec_sandbox",
    "model.codex_exec_profile": "codex_exec_profile",
    "model.codex_exec_full_auto": "codex_exec_full_auto",
    "model.codex_exec_reasoning_effort": "codex_exec_reasoning_effort",
    "model.codex_exec_use_sdk": "codex_exec_use_sdk",
    "model.codex_exec_network_access": "codex_exec_network_access",
    "model.codex_exec_web_search": "codex_exec_web_search",
    "model.codex_exec_approval_policy": "codex_exec_approval_policy",
    "model.codex_trace_to_optimizer": "codex_trace_to_optimizer",
    "model.azure_endpoint": "azure_endpoint",
    "model.azure_api_version": "azure_api_version",
    "model.azure_api_key": "azure_api_key",
    "model.azure_openai_endpoint": "azure_openai_endpoint",
    "model.azure_openai_api_version": "azure_openai_api_version",
    "model.azure_openai_api_key": "azure_openai_api_key",
    "model.azure_openai_auth_mode": "azure_openai_auth_mode",
    "model.azure_openai_ad_scope": "azure_openai_ad_scope",
    "model.azure_openai_managed_identity_client_id": "azure_openai_managed_identity_client_id",
    "model.optimizer_azure_openai_endpoint": "optimizer_azure_openai_endpoint",
    "model.optimizer_azure_openai_api_version": "optimizer_azure_openai_api_version",
    "model.optimizer_azure_openai_api_key": "optimizer_azure_openai_api_key",
    "model.optimizer_azure_openai_auth_mode": "optimizer_azure_openai_auth_mode",
    "model.optimizer_azure_openai_ad_scope": "optimizer_azure_openai_ad_scope",
    "model.optimizer_azure_openai_managed_identity_client_id": "optimizer_azure_openai_managed_identity_client_id",
    "model.target_azure_openai_endpoint": "target_azure_openai_endpoint",
    "model.target_azure_openai_api_version": "target_azure_openai_api_version",
    "model.target_azure_openai_api_key": "target_azure_openai_api_key",
    "model.target_azure_openai_auth_mode": "target_azure_openai_auth_mode",
    "model.target_azure_openai_ad_scope": "target_azure_openai_ad_scope",
    "model.target_azure_openai_managed_identity_client_id": "target_azure_openai_managed_identity_client_id",
    "train.num_epochs": "num_epochs",
    "train.train_size": "train_size",
    "train.steps_per_epoch": "steps_per_epoch",
    "train.batch_size": "batch_size",
    "train.accumulation": "accumulation",
    "train.seed": "seed",
    "evaluation.test_env_num": "test_env_num",
    "env.name": "env",
    "env.skill_init": "skill_init",
    "env.out_root": "out_root",
}


# ── Deep merge ───────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base* (returns new dict)."""
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


# ── YAML loading with _base_ inheritance ─────────────────────────────────

def _load_yaml(path: str, _visited: set[str] | None = None) -> dict:
    """Load a YAML file, resolving ``_base_`` inheritance recursively."""
    abs_path = os.path.abspath(path)
    if _visited is None:
        _visited = set()
    if abs_path in _visited:
        raise ValueError(f"Circular _base_ inheritance: {abs_path}")
    _visited.add(abs_path)

    with open(abs_path) as f:
        cfg = yaml.safe_load(f) or {}

    base_ref = cfg.pop("_base_", None)
    if base_ref:
        base_path = os.path.join(os.path.dirname(abs_path), base_ref)
        base_cfg = _load_yaml(base_path, _visited)
        cfg = _deep_merge(base_cfg, cfg)

    return cfg


# ── Format detection ─────────────────────────────────────────────────────

def is_structured(cfg: dict) -> bool:
    """Return True if *cfg* uses the new structured section format."""
    return any(
        key in _STRUCTURED_SECTIONS and isinstance(cfg.get(key), dict)
        for key in cfg
    )


# ── Flatten ──────────────────────────────────────────────────────────────

def flatten_config(cfg: dict) -> dict:
    """Convert a structured config to the flat dict expected by the trainer.

    If *cfg* is already flat, returns a shallow copy unchanged.
    """
    if not is_structured(cfg):
        removed_flat = sorted(key for key in _REMOVED_FLAT_SKILLOPT_KEYS if key in cfg)
        if removed_flat:
            raise ValueError(
                "Removed SkillOpt config entries are no longer supported: "
                + ", ".join(removed_flat)
            )
        return dict(cfg)

    flat: dict[str, Any] = {}

    removed_sections = sorted(section for section in _REMOVED_SKILLOPT_SECTIONS if section in cfg)
    removed_keys: list[str] = []
    for dotted in _REMOVED_SKILLOPT_KEYS:
        section, key = dotted.split(".", 1)
        section_dict = cfg.get(section, {})
        if isinstance(section_dict, dict) and key in section_dict:
            removed_keys.append(dotted)
    if removed_sections or removed_keys:
        parts = [*removed_sections, *sorted(removed_keys)]
        raise ValueError(
            "Removed SkillOpt config entries are no longer supported: "
            + ", ".join(parts)
        )

    # Apply the explicit mapping
    for dotted, flat_key in _FLATTEN_MAP.items():
        section, key = dotted.split(".", 1)
        section_dict = cfg.get(section, {})
        if isinstance(section_dict, dict) and key in section_dict:
            flat[flat_key] = section_dict[key]

    # Pass through env-specific keys not in the explicit mapping
    env_section = cfg.get("env", {})
    if isinstance(env_section, dict):
        mapped_env_keys = {
            k.split(".", 1)[1]
            for k in _FLATTEN_MAP
            if k.startswith("env.")
        }
        for key, val in env_section.items():
            if key not in mapped_env_keys:
                flat[key] = val

    return flat


# ── Override application ─────────────────────────────────────────────────

def _cast_value(val_str: str) -> Any:
    """Auto-cast a CLI string value to int / float / bool / str."""
    if val_str.lower() in ("true", "yes"):
        return True
    if val_str.lower() in ("false", "no"):
        return False
    try:
        return int(val_str)
    except ValueError:
        pass
    try:
        return float(val_str)
    except ValueError:
        pass
    return val_str


def apply_overrides(cfg: dict, overrides: list[str]) -> None:
    """Apply ``key=value`` overrides to a structured config (in place).

    Supports both ``section.key=value`` (for structured configs) and
    ``key=value`` (for flat configs or flat keys in env section).
    """
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid override (expected key=value): {item!r}")
        key, val_str = item.split("=", 1)
        val = _cast_value(val_str)

        if "." in key:
            section, subkey = key.split(".", 1)
            if section in cfg and isinstance(cfg[section], dict):
                cfg[section][subkey] = val
            else:
                cfg.setdefault(section, {})[subkey] = val
        else:
            # Flat key — apply to top level (for legacy compat)
            cfg[key] = val


# ── Public API ───────────────────────────────────────────────────────────

def load_config(
    path: str,
    overrides: list[str] | None = None,
) -> dict:
    """Load a config file with ``_base_`` inheritance and optional overrides.

    Parameters
    ----------
    path : str
        Path to the YAML config file.
    overrides : list[str] | None
        ``key=value`` strings from ``--cfg-options``.

    Returns
    -------
    dict
        The merged config (structured or flat depending on the YAML).
    """
    cfg = _load_yaml(path)
    if overrides:
        apply_overrides(cfg, overrides)
    return cfg
