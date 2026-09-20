"""Model backend configuration for graphskillevo."""
from __future__ import annotations

import os

from graphskillevo.model import (
    configure_azure_openai,
    configure_codex_exec,
    set_optimizer_backend,
    set_optimizer_deployment,
    set_reasoning_effort,
    set_target_backend,
    set_target_deployment,
)


def configure_models(cfg: dict) -> None:
    backend = cfg.get("model_backend", "azure_openai")
    configure_azure_openai(
        endpoint=cfg.get("azure_openai_endpoint") or cfg.get("azure_endpoint") or None,
        api_version=cfg.get("azure_openai_api_version") or cfg.get("azure_api_version") or None,
        api_key=cfg.get("azure_openai_api_key") or cfg.get("azure_api_key") or None,
        auth_mode=cfg.get("azure_openai_auth_mode") or None,
        ad_scope=cfg.get("azure_openai_ad_scope") or None,
        managed_identity_client_id=cfg.get("azure_openai_managed_identity_client_id") or None,
        optimizer_endpoint=cfg.get("optimizer_azure_openai_endpoint") or None,
        optimizer_api_version=cfg.get("optimizer_azure_openai_api_version") or None,
        optimizer_api_key=cfg.get("optimizer_azure_openai_api_key") or None,
        optimizer_auth_mode=cfg.get("optimizer_azure_openai_auth_mode") or None,
        optimizer_ad_scope=cfg.get("optimizer_azure_openai_ad_scope") or None,
        optimizer_managed_identity_client_id=cfg.get("optimizer_azure_openai_managed_identity_client_id") or None,
        target_endpoint=cfg.get("target_azure_openai_endpoint") or None,
        target_api_version=cfg.get("target_azure_openai_api_version") or None,
        target_api_key=cfg.get("target_azure_openai_api_key") or None,
        target_auth_mode=cfg.get("target_azure_openai_auth_mode") or None,
        target_ad_scope=cfg.get("target_azure_openai_ad_scope") or None,
        target_managed_identity_client_id=cfg.get("target_azure_openai_managed_identity_client_id") or None,
    )

    optimizer_backend = cfg.get("optimizer_backend")
    target_backend = cfg.get("target_backend")
    if not optimizer_backend or not target_backend:
        if backend in {"codex", "codex_exec"}:
            optimizer_backend = optimizer_backend or "openai_chat"
            target_backend = target_backend or "codex_exec"
        else:
            optimizer_backend = optimizer_backend or "openai_chat"
            target_backend = target_backend or "openai_chat"
        cfg["optimizer_backend"] = optimizer_backend
        cfg["target_backend"] = target_backend

    if optimizer_backend != "openai_chat":
        raise ValueError("optimizer_backend must be openai_chat")
    if target_backend not in {"openai_chat", "codex_exec"}:
        raise ValueError("target_backend must be openai_chat or codex_exec")

    set_optimizer_backend(optimizer_backend)
    set_target_backend(target_backend)
    set_optimizer_deployment(cfg["optimizer_model"])
    set_target_deployment(cfg["target_model"])

    configure_codex_exec(
        path=cfg.get("codex_exec_path", "codex"),
        sandbox=cfg.get("codex_exec_sandbox", "workspace-write"),
        profile=cfg.get("codex_exec_profile", ""),
        full_auto=cfg.get("codex_exec_full_auto", False),
        reasoning_effort=cfg.get("codex_exec_reasoning_effort", "none"),
        use_sdk=cfg.get("codex_exec_use_sdk", None),
        network_access=cfg.get("codex_exec_network_access", False),
        web_search=cfg.get("codex_exec_web_search", False),
        approval_policy=cfg.get("codex_exec_approval_policy", "never"),
    )
    os.environ["REFLACT_CODEX_TRACE_TO_OPTIMIZER"] = (
        "1" if target_backend == "codex_exec" and cfg.get("codex_trace_to_optimizer", False) else "0"
    )
    set_reasoning_effort(cfg.get("reasoning_effort", "") or None)
