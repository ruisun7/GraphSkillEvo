"""Model router for GraphSkillEvo."""
from __future__ import annotations

from typing import Any

from graphskillevo.model import azure_openai as _openai
from graphskillevo.model.backend_config import (  # noqa: F401
    configure_codex_exec,
    get_codex_exec_config,
    get_optimizer_backend,
    get_target_backend,
    is_optimizer_chat_backend,
    is_target_chat_backend,
    is_target_exec_backend,
    set_optimizer_backend,
    set_target_backend,
)


def set_backend(name: str | None) -> str:
    normalized = str(name or "openai_chat").strip().lower()
    if normalized in {"azure", "azure_openai", "azure-openai", "openai", "openai_chat"}:
        set_optimizer_backend("openai_chat")
        set_target_backend("openai_chat")
        return "openai_chat"
    if normalized in {"codex", "codex_exec"}:
        set_optimizer_backend("openai_chat")
        set_target_backend("codex_exec")
        return "codex_exec"
    raise ValueError(f"Unsupported backend: {name!r}")


def get_backend_name() -> str:
    target = get_target_backend()
    return "codex_exec" if target == "codex_exec" else "openai_chat"


def chat_optimizer(
    system: str,
    user: str,
    max_completion_tokens: int = 16384,
    retries: int = 5,
    stage: str = "optimizer",
    reasoning_effort: str | None = None,
    timeout: int | None = None,
) -> tuple[str, dict]:
    if get_optimizer_backend() != "openai_chat":
        raise ValueError("optimizer_backend must be openai_chat")
    return _openai.chat_optimizer(
        system=system,
        user=user,
        max_completion_tokens=max_completion_tokens,
        retries=retries,
        stage=stage,
        reasoning_effort=reasoning_effort,
        timeout=timeout,
    )


def chat_target(
    system: str,
    user: str,
    max_completion_tokens: int = 16384,
    retries: int = 5,
    stage: str = "target",
    reasoning_effort: str | None = None,
    timeout: int | None = None,
) -> tuple[str, dict]:
    if get_target_backend() != "openai_chat":
        raise NotImplementedError("chat_target requires target_backend=openai_chat")
    return _openai.chat_target(
        system=system,
        user=user,
        max_completion_tokens=max_completion_tokens,
        retries=retries,
        stage=stage,
        reasoning_effort=reasoning_effort,
        timeout=timeout,
    )


def chat_optimizer_messages(
    messages: list[dict[str, Any]],
    max_completion_tokens: int = 16384,
    retries: int = 5,
    stage: str = "optimizer",
    reasoning_effort: str | None = None,
    *,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
    return_message: bool = False,
    timeout: int | None = None,
) -> tuple[Any, dict]:
    if get_optimizer_backend() != "openai_chat":
        raise ValueError("optimizer_backend must be openai_chat")
    return _openai.chat_optimizer_messages(
        messages=messages,
        max_completion_tokens=max_completion_tokens,
        retries=retries,
        stage=stage,
        reasoning_effort=reasoning_effort,
        tools=tools,
        tool_choice=tool_choice,
        return_message=return_message,
        timeout=timeout,
    )


def chat_target_messages(
    messages: list[dict[str, Any]],
    max_completion_tokens: int = 16384,
    retries: int = 5,
    stage: str = "target",
    reasoning_effort: str | None = None,
    *,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
    return_message: bool = False,
    timeout: int | None = None,
) -> tuple[Any, dict]:
    if get_target_backend() != "openai_chat":
        raise NotImplementedError("chat_target_messages requires target_backend=openai_chat")
    return _openai.chat_target_messages(
        messages=messages,
        max_completion_tokens=max_completion_tokens,
        retries=retries,
        stage=stage,
        reasoning_effort=reasoning_effort,
        tools=tools,
        tool_choice=tool_choice,
        return_message=return_message,
        timeout=timeout,
    )


def chat_messages_with_deployment(*args, **kwargs):
    return _openai.chat_messages_with_deployment(*args, **kwargs)


def chat_with_deployment(*args, **kwargs):
    return _openai.chat_with_deployment(*args, **kwargs)


def configure_azure_openai(**kwargs) -> None:
    _openai.configure_azure_openai(**kwargs)


def get_token_summary() -> dict:
    return _openai.get_token_summary()


def reset_token_tracker() -> None:
    _openai.reset_token_tracker()


def set_reasoning_effort(effort: str | None) -> None:
    _openai.set_reasoning_effort(effort)


def set_target_deployment(deployment: str) -> None:
    _openai.set_target_deployment(deployment)


def set_optimizer_deployment(deployment: str) -> None:
    _openai.set_optimizer_deployment(deployment)
