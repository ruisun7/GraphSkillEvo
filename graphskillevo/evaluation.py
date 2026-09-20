"""Benchmark evaluation helpers for graphskillevo."""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BatchSpec:
    phase: str
    split: str
    seed: int
    batch_size: int
    payload: object | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def compute_score(results: list) -> tuple[float, float]:
    if not results:
        return 0.0, 0.0

    def _hard(row: object) -> float:
        return float(row.hard if hasattr(row, "hard") else row.get("hard", 0))

    def _soft(row: object) -> float:
        return float(row.soft if hasattr(row, "soft") else row.get("soft", 0.0))

    return (
        sum(_hard(row) for row in results) / len(results),
        sum(_soft(row) for row in results) / len(results),
    )


@dataclass(slots=True)
class EvaluationResult:
    hard: float
    soft: float
    n: int
    out_dir: str
    examples: list[dict] = field(default_factory=list)
    reflection_context: str = ""

    def to_record(self) -> dict:
        return {
            "hard": self.hard,
            "soft": self.soft,
            "n": self.n,
            "out_dir": self.out_dir,
            "examples": self.examples,
            "reflection_context": self.reflection_context,
        }


def _clip_text(value: object, limit: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def _score_value(row: object, key: str) -> float:
    if hasattr(row, key):
        return float(getattr(row, key) or 0.0)
    if isinstance(row, dict):
        return float(row.get(key, 0.0) or 0.0)
    return 0.0


def _row_value(row: object, key: str, default: object = "") -> object:
    if hasattr(row, key):
        return getattr(row, key)
    if isinstance(row, dict):
        return row.get(key, default)
    return default


def _format_conversation_snippet(conversation: object, max_chars: int = 1800) -> str:
    if not isinstance(conversation, list):
        return ""
    lines: list[str] = []
    for item in conversation:
        if not isinstance(item, dict):
            lines.append(f"[agent] {_clip_text(item, 400)}")
            continue
        if item.get("type") == "tool_call":
            lines.append(f"[action] {_clip_text(item.get('cmd'), 240)}")
            lines.append(f"[obs] {_clip_text(item.get('obs'), 360)}")
        elif "action" in item and "env_feedback" in item:
            step = item.get("step", "?")
            reasoning = _clip_text(item.get("reasoning"), 240)
            if reasoning:
                lines.append(f"[step {step} think] {reasoning}")
            lines.append(f"[step {step} action] {_clip_text(item.get('action'), 220)}")
            lines.append(f"[step {step} obs] {_clip_text(item.get('env_feedback'), 360)}")
        else:
            role = item.get("role", "agent")
            content = item.get("content", "")
            lines.append(f"[{role}] {_clip_text(content, 420)}")
    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n...[middle truncated]...\n" + text[-half:]


def _conversation_snippet(out_dir: str, task_id: str) -> str:
    if not task_id:
        return ""
    path = os.path.join(out_dir, "predictions", task_id, "conversation.json")
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return _format_conversation_snippet(json.load(f))
    except (OSError, json.JSONDecodeError):
        return ""


def _read_prediction_text(prediction_dir: str, task_id: str, filename: str) -> str:
    path = os.path.join(prediction_dir, task_id, filename)
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def fmt_trajectory(conversation: object, max_chars: int = 12_000) -> str:
    if not isinstance(conversation, list):
        return ""
    lines: list[str] = []
    for item in conversation:
        if not isinstance(item, dict):
            lines.append(f"[agent] {_clip_text(item, 500)}")
            continue
        if item.get("type") == "tool_call":
            lines.append(f"[action] {_clip_text(item.get('cmd'), 500)}")
            lines.append(f"[obs]    {_clip_text(item.get('obs'), 800)}")
        elif "action" in item and "env_feedback" in item:
            step = item.get("step", "?")
            reasoning = _clip_text(item.get("reasoning"), 300)
            action = _clip_text(item.get("action"), 200)
            feedback = _clip_text(item.get("env_feedback"), 500)
            if reasoning:
                lines.append(f"[step {step} think] {reasoning}")
            lines.append(f"[step {step} action] {action}")
            lines.append(f"[step {step} obs]    {feedback}")
        elif item.get("role") == "system":
            lines.append(f"[verification] {_clip_text(item.get('content'), 2000)}")
        else:
            role = item.get("role", "agent")
            lines.append(f"[{role}] {_clip_text(item.get('content'), 500)}")

    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n...[middle truncated]...\n" + text[-half:]


def fmt_minibatch_trajectories(items: list[dict], prediction_dir: str) -> str:
    parts: list[str] = []
    for idx, item in enumerate(items, 1):
        task_id = str(item.get("id") or "")
        if not task_id:
            continue
        conv_path = os.path.join(prediction_dir, task_id, "conversation.json")
        if not os.path.isfile(conv_path):
            continue
        try:
            with open(conv_path, encoding="utf-8") as f:
                trajectory = fmt_trajectory(json.load(f))
        except (OSError, json.JSONDecodeError):
            continue
        if not trajectory.strip():
            continue

        header = (
            f"### Trajectory {idx} (id={task_id})\n"
            f"Task: {item.get('task_description', item.get('instruction', ''))}\n"
            f"Task type: {item.get('task_type', item.get('instruction_type', ''))}\n"
        )
        fail_reason = str(item.get("fail_reason") or "").strip()
        if fail_reason:
            header += f"Failure reason: {fail_reason}\n"
        header += f"Steps: {item.get('n_turns', '?')}\n"

        reference_text = str(item.get("reference_text") or "").strip()
        if reference_text:
            header += f"\n#### Hidden Reference\n{reference_text[:4000]}\n"

        target_prompt = str(item.get("target_system_prompt") or "").strip()
        if not target_prompt:
            target_prompt = _read_prediction_text(prediction_dir, task_id, "target_system_prompt.txt")
        if target_prompt:
            header += f"\n#### Target System Prompt\n{target_prompt[:3000]}\n"

        user_prompt = str(item.get("target_user_prompt") or "").strip()
        if not user_prompt:
            user_prompt = _read_prediction_text(prediction_dir, task_id, "target_user_prompt.txt")
        if user_prompt:
            header += f"\n#### Target User Prompt\n{user_prompt[:3000]}\n"

        if os.environ.get("REFLACT_CODEX_TRACE_TO_OPTIMIZER", "0") == "1":
            codex_trace_summary = str(item.get("codex_trace_summary") or "").strip()
            if not codex_trace_summary:
                codex_trace_summary = _read_prediction_text(prediction_dir, task_id, "codex_trace_summary.txt")
            if codex_trace_summary:
                header += f"\n#### Codex Trace Summary\n{codex_trace_summary}\n"

        codex_probe_trace_steps = str(item.get("codex_probe_trace_steps") or "").strip()
        if codex_probe_trace_steps:
            header += f"\n#### Codex Trace Steps\n{codex_probe_trace_steps}\n"

        spreadsheet_preview = str(item.get("spreadsheet_preview") or "").strip()
        if not spreadsheet_preview:
            spreadsheet_preview = _read_prediction_text(prediction_dir, task_id, "spreadsheet_preview.txt")
        if spreadsheet_preview:
            header += f"\n#### Spreadsheet Preview\n{spreadsheet_preview[:3000]}\n"

        parts.append(header + "\n" + trajectory)
    return "\n\n---\n\n".join(parts)


def _sample_failure_rows(results: list, *, failure_k: int, seed: int) -> list:
    if failure_k <= 0:
        return []
    failures = [row for row in results if _score_value(row, "hard") < 1e-9]
    return random.Random(seed).sample(failures, k=min(failure_k, len(failures)))


def summarize_rollout_examples(
    results: list,
    out_dir: str,
    *,
    failure_k: int = 3,
    seed: int = 0,
) -> list[dict]:
    """Build a compact success/failure summary from already completed rollout outputs."""
    selected_failures = _sample_failure_rows(results, failure_k=failure_k, seed=seed)
    examples: list[dict] = []
    for row in selected_failures:
        task_id = str(_row_value(row, "id", ""))
        examples.append(
            {
                "id": task_id,
                "outcome": "failure",
                "hard": _score_value(row, "hard"),
                "soft": _score_value(row, "soft"),
                "task_type": _clip_text(_row_value(row, "task_type", _row_value(row, "instruction_type", "")), 160),
                "failure_reason": _clip_text(_row_value(row, "fail_reason", ""), 500),
                "task": _clip_text(
                    _row_value(row, "task_description", _row_value(row, "instruction", "")),
                    700,
                ),
                "trajectory_snippet": _conversation_snippet(out_dir, task_id),
            }
        )
    return examples


def _safe_payload_items(payload: object | None) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list | tuple):
        return [dict(item) for item in payload if isinstance(item, dict)]
    return []


def _items_from_env(env: object) -> list[dict]:
    if isinstance(env, list | tuple):
        return [dict(item) for item in env if isinstance(item, dict)]
    items = getattr(env, "items", None)
    if isinstance(items, list | tuple):
        return [dict(item) for item in items if isinstance(item, dict)]
    return []


def _row_to_reflection_item(row: object, source_item: dict | None = None) -> dict:
    if isinstance(row, dict):
        data = dict(row)
    else:
        data = {}
        for key in (
            "id",
            "task_description",
            "instruction",
            "question",
            "task_type",
            "instruction_type",
            "fail_reason",
            "n_turns",
            "reference_text",
            "target_system_prompt",
            "target_user_prompt",
            "spreadsheet_preview",
            "hard",
            "soft",
        ):
            if hasattr(row, key):
                data[key] = getattr(row, key)

    source_item = source_item or {}
    data["id"] = str(data.get("id") or source_item.get("id") or "")
    if not data.get("task_description"):
        data["task_description"] = (
            data.get("instruction")
            or data.get("question")
            or source_item.get("task_description")
            or source_item.get("instruction")
            or source_item.get("question")
            or ""
        )
    if not data.get("task_type"):
        data["task_type"] = (
            data.get("instruction_type")
            or source_item.get("task_type")
            or source_item.get("instruction_type")
            or source_item.get("subtask")
            or source_item.get("theorem_type")
            or ""
        )
    if "fail_reason" not in data:
        data["fail_reason"] = ""
    if "n_turns" not in data:
        data["n_turns"] = "?"
    return data


def _build_reflection_items(
    *,
    selected_failures: list,
    source_items: list[dict],
    adapter: object,
    include_hidden_reference: bool = True,
) -> list[dict]:
    item_by_id = {
        str(item.get("id")): item
        for item in source_items
        if isinstance(item, dict) and item.get("id") is not None
    }
    build_reference_text = getattr(adapter, "build_reference_text", None)

    reflection_items: list[dict] = []
    for row in selected_failures:
        row_id = str(_row_value(row, "id", ""))
        source_item = item_by_id.get(row_id)
        data = _row_to_reflection_item(row, source_item)
        if not include_hidden_reference:
            data.pop("reference_text", None)
        if include_hidden_reference and source_item and not data.get("reference_text"):
            reference_text = ""
            if callable(build_reference_text):
                try:
                    reference_text = str(build_reference_text(source_item) or "").strip()
                except Exception:
                    reference_text = ""
            if not reference_text:
                reference_text = str(source_item.get("reference_text") or "").strip()
            if reference_text:
                data["reference_text"] = reference_text
        reflection_items.append(data)
    return reflection_items


def build_rollout_reflection_context(
    results: list,
    out_dir: str,
    *,
    source_items: list[dict] | None = None,
    adapter: object | None = None,
    failure_k: int = 3,
    seed: int = 0,
    include_hidden_reference: bool = True,
) -> str:
    """Build GraphSkillEvo-style reflection text from selected failed rollout outputs."""
    selected_failures = _sample_failure_rows(results, failure_k=failure_k, seed=seed)
    if not selected_failures:
        return ""

    reflection_items = _build_reflection_items(
        selected_failures=selected_failures,
        source_items=source_items or [],
        adapter=adapter,
        include_hidden_reference=include_hidden_reference,
    )
    return fmt_minibatch_trajectories(
        reflection_items,
        os.path.join(out_dir, "predictions"),
    )


class SkillEvaluator:
    def __init__(self, adapter, dataloader, out_root: str, seed: int) -> None:
        self.adapter = adapter
        self.dataloader = dataloader
        self.out_root = out_root
        self.seed = int(seed)

    def _build_train_env(self, env_num: int, seed: int):
        if self.dataloader is not None:
            batch_size = env_num or self.dataloader.get_train_size()
            batch = self.dataloader.build_train_batch(
                batch_size=batch_size,
                seed=seed,
                out_root=self.out_root,
            )
            env = self.adapter.build_env_from_batch(batch, out_root=self.out_root)
            return env, batch.batch_size, _safe_payload_items(batch.payload)
        env = self.adapter.build_train_env(batch_size=env_num, seed=seed, out_root=self.out_root)
        actual_n = len(env) if hasattr(env, "__len__") else env_num
        return env, actual_n, _items_from_env(env)

    def _build_eval_env(self, split: str, env_num: int, seed: int):
        if self.dataloader is not None:
            batch = self.dataloader.build_eval_batch(
                env_num=env_num,
                split=split,
                seed=seed,
                out_root=self.out_root,
            )
            env = self.adapter.build_env_from_batch(batch, out_root=self.out_root)
            return env, batch.batch_size, _safe_payload_items(batch.payload)
        env = self.adapter.build_eval_env(
            env_num=env_num,
            split=split,
            seed=seed,
            out_root=self.out_root,
        )
        actual_n = len(env) if hasattr(env, "__len__") else env_num
        return env, actual_n, _items_from_env(env)

    def evaluate(
        self,
        *,
        skill_content: str,
        split: str,
        env_num: int,
        seed: int,
        out_dir: str,
        reflection_failure_k: int = 3,
        include_hidden_reference: bool = True,
    ) -> EvaluationResult:
        if split == "train":
            env, actual_n, source_items = self._build_train_env(env_num, seed)
        else:
            env, actual_n, source_items = self._build_eval_env(split, env_num, seed)
        if split == "train" and reflection_failure_k >= actual_n:
            raise ValueError(
                "reflection_failure_k must be smaller than the actual train sample count "
                f"(got k={reflection_failure_k}, n={actual_n})"
            )
        os.makedirs(out_dir, exist_ok=True)
        results = self.adapter.rollout(env, skill_content, out_dir, use_eval_feedback=False)
        hard, soft = compute_score(results)
        return EvaluationResult(
            hard=hard,
            soft=soft,
            n=actual_n,
            out_dir=out_dir,
            examples=summarize_rollout_examples(results, out_dir, failure_k=reflection_failure_k, seed=seed),
            reflection_context=build_rollout_reflection_context(
                results,
                out_dir,
                source_items=source_items,
                adapter=self.adapter,
                failure_k=reflection_failure_k,
                seed=seed,
                include_hidden_reference=include_hidden_reference,
            ),
        )
