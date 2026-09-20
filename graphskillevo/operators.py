"""LLM-backed initialization, crossover, and mutation operators."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from graphskillevo.graph_skill import adopt_graph, adopt_other, assert_graph_skill
from graphskillevo.prompts import load_prompt as _load_prompt


@dataclass(slots=True)
class OperatorResult:
    new_skill: str
    prompt: str
    raw_response: str
    parsed: dict
    usage: dict


class GraphSkillGenerationError(ValueError):
    """Raised when an LLM response is syntactically valid but not graph-structured."""

    def __init__(
        self,
        message: str,
        *,
        prompt: str = "",
        raw_response: str = "",
        parsed: dict | None = None,
        usage: dict | None = None,
        candidate: str = "",
    ) -> None:
        super().__init__(message)
        self.prompt = prompt
        self.raw_response = raw_response
        self.parsed = parsed or {}
        self.usage = usage or {}
        self.candidate = candidate

    def to_record(self) -> dict:
        return {
            "error": str(self),
            "prompt": self.prompt,
            "raw_response": self.raw_response,
            "parsed": self.parsed,
            "usage": self.usage,
            "candidate": self.candidate,
        }


def load_prompt(name: str, env: str | None = None) -> str:
    return _load_prompt(name, env=env)


def _normalize_task_prompt_env(env_name: str | None) -> str:
    env_key = str(env_name or "").strip().lower().replace("-", "_")
    aliases = {
        "livemath": "livemathematicianbench",
        "live_math": "livemathematicianbench",
        "live_mathematician_bench": "livemathematicianbench",
    }
    return aliases.get(env_key, env_key)


def load_default_mutation_task_guidance(env_name: str | None) -> str:
    env_key = _normalize_task_prompt_env(env_name)
    if not env_key:
        return ""
    prompt_name = f"mutation_task_extra_{env_key}"
    try:
        return load_prompt(prompt_name, env=env_key).strip()
    except FileNotFoundError:
        return ""


def extract_json(text: str) -> dict | None:
    fenced = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    bare = re.search(r"\{.*\}", text, re.DOTALL)
    if bare:
        try:
            return json.loads(bare.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _format_reflection_context(context: str | dict | None) -> str:
    if not context:
        return ""
    if isinstance(context, str):
        return context.strip()
    direct_context = str(context.get("reflection_context") or "").strip()
    if direct_context:
        return direct_context
    parent_texts = []
    for parent in context.get("selected_parents", []):
        if isinstance(parent, dict):
            text = str(parent.get("train_reflection_context") or "").strip()
            if text:
                parent_texts.append(text)
    return "\n\n---\n\n".join(parent_texts)


class EvolutionOperators:
    def __init__(
        self,
        *,
        env_name: str,
        max_completion_tokens: int,
        reasoning_effort: str | None,
        graph_retry_attempts: int = 3,
    ) -> None:
        self.env_name = env_name
        self.max_completion_tokens = int(max_completion_tokens)
        self.reasoning_effort = reasoning_effort or None
        self.graph_retry_attempts = max(1, int(graph_retry_attempts))

    def initialize_population(
        self,
        *,
        n: int,
        base_skill: str,
        task_context: str = "",
    ) -> tuple[list[str], dict]:
        if n <= 0:
            return [], {"prompt": "", "raw_response": "", "parsed": {"skills": []}, "usage": {}}
        system = load_prompt("init_population")
        from graphskillevo.model import chat_optimizer

        accepted: list[str] = []
        attempts: list[dict] = []
        discarded: list[dict] = []
        assert_graph_skill_failure_count = 0
        last_prompt = ""
        last_response = ""
        last_parsed: dict = {}
        last_usage: dict = {}

        while len(accepted) < n:
            requested = n - len(accepted)
            attempt_no = len(attempts) + 1
            user = self._build_init_user(
                n=requested,
                base_skill=base_skill,
                task_context=task_context,
                recent_errors=discarded[-3:],
            )
            response, usage = chat_optimizer(
                system=system,
                user=user,
                max_completion_tokens=self.max_completion_tokens,
                retries=3,
                stage="graphskillevo_graph_init_population",
                reasoning_effort=self.reasoning_effort,
            )
            parsed = extract_json(response)
            last_prompt = user
            last_response = response
            last_parsed = parsed if isinstance(parsed, dict) else {}
            last_usage = usage
            attempt_record = {
                "attempt": attempt_no,
                "requested": requested,
                "prompt": user,
                "raw_response": response,
                "parsed": last_parsed,
                "usage": usage,
                "accepted_count": 0,
                "assert_graph_skill_failure_count": 0,
                "discarded": [],
            }
            if not isinstance(parsed, dict) or not isinstance(parsed.get("skills"), list):
                error = "init_population response did not contain JSON object with a skills list"
                discard = {
                    "attempt": attempt_no,
                    "index": None,
                    "error": error,
                    "skill": "",
                }
                attempt_record["discarded"].append(discard)
                discarded.append(discard)
                attempts.append(attempt_record)
                continue

            for idx, item in enumerate(parsed["skills"]):
                skill = str(item).rstrip() + "\n"
                if not skill.strip():
                    discard = {
                        "attempt": attempt_no,
                        "index": idx,
                        "error": "empty skill",
                        "skill": "",
                    }
                    attempt_record["discarded"].append(discard)
                    discarded.append(discard)
                    continue
                try:
                    assert_graph_skill(skill)
                except ValueError as exc:
                    assert_graph_skill_failure_count += 1
                    attempt_record["assert_graph_skill_failure_count"] += 1
                    discard = {
                        "attempt": attempt_no,
                        "index": idx,
                        "failure_type": "assert_graph_skill",
                        "error": str(exc),
                        "skill": skill,
                    }
                    attempt_record["discarded"].append(discard)
                    discarded.append(discard)
                    continue
                if len(accepted) < n:
                    accepted.append(skill)
                    attempt_record["accepted_count"] += 1
                else:
                    discard = {
                        "attempt": attempt_no,
                        "index": idx,
                        "error": "extra valid skill ignored after requested population was filled",
                        "skill": skill,
                    }
                    attempt_record["discarded"].append(discard)
                    discarded.append(discard)
            attempts.append(attempt_record)
            if len(accepted) < n and attempt_record["assert_graph_skill_failure_count"]:
                print(
                    f"  [init retry] assert_graph_skill rejected "
                    f"{attempt_record['assert_graph_skill_failure_count']} skill(s) "
                    f"on attempt={attempt_no}; regenerating remaining={n - len(accepted)}"
                )

        return accepted[:n], {
            "prompt": last_prompt,
            "raw_response": last_response,
            "parsed": last_parsed,
            "usage": last_usage,
            "accepted_count": n,
            "attempt_count": len(attempts),
            "retry_count": max(0, len(attempts) - 1),
            "assert_graph_skill_failure_count": assert_graph_skill_failure_count,
            "discarded_skills": discarded,
            "attempts": attempts,
        }

    def _build_init_user(
        self,
        *,
        n: int,
        base_skill: str,
        task_context: str,
        recent_errors: list[dict],
    ) -> str:
        user = (
            f"Environment: {self.env_name}\n"
            f"Number of skills to generate: {n}\n\n"
        )
        if base_skill.strip():
            user += f"## Reference/base skill\n{base_skill}\n\n"
        if task_context.strip():
            user += f"## Task context\n{task_context}\n\n"
        if recent_errors:
            user += (
                "## Previous invalid outputs to avoid\n"
                f"{json.dumps(recent_errors, ensure_ascii=False, indent=2)}\n\n"
            )
        user += (
            "Generate diverse complete skill documents. "
            "Return JSON only with shape {\"skills\": [\"...\"]}."
        )
        return user

    def mutation_other(self, *, parent: str, context: str | dict | None = None) -> OperatorResult:
        system, user = self._build_mutation_prompt(
            scope="other",
            parent=parent,
            context=context,
        )
        return self._single_skill_operator(
            system=system,
            user=user,
            stage="graphskillevo_graph_mutation_other",
            scope="other",
            parent_a=parent,
        )

    def mutation_graph(self, *, parent: str, context: str | dict | None = None) -> OperatorResult:
        system, user = self._build_mutation_prompt(
            scope="graph",
            parent=parent,
            context=context,
        )
        return self._single_skill_operator(
            system=system,
            user=user,
            stage="graphskillevo_graph_mutation_graph",
            scope="graph",
            parent_a=parent,
        )

    def crossover_other(self, *, parent_a: str, parent_b: str, context: dict | None = None) -> OperatorResult:
        del context
        system = load_prompt("crossover_other")
        user = (
            f"Environment: {self.env_name}\n\n"
            f"## Parent A\n{parent_a}\n\n"
            f"## Parent B\n{parent_b}\n\n"
        )
        user += "Return JSON only with shape {\"new_skill\": \"...\", \"notes\": [\"...\"]}."
        return self._single_skill_operator(
            system=system,
            user=user,
            stage="graphskillevo_graph_crossover_other",
            scope="other",
            parent_a=parent_a,
        )

    def crossover_graph(self, *, parent_a: str, parent_b: str, context: dict | None = None) -> OperatorResult:
        del context
        system = load_prompt("crossover_graph")
        user = (
            f"Environment: {self.env_name}\n\n"
            f"## Parent A\n{parent_a}\n\n"
            f"## Parent B\n{parent_b}\n\n"
        )
        user += "Return JSON only with shape {\"new_skill\": \"...\", \"notes\": [\"...\"]}."
        return self._single_skill_operator(
            system=system,
            user=user,
            stage="graphskillevo_graph_crossover_graph",
            scope="graph",
            parent_a=parent_a,
        )

    def _single_skill_operator(
        self,
        *,
        system: str,
        user: str,
        stage: str,
        scope: str,
        parent_a: str,
    ) -> OperatorResult:
        from graphskillevo.model import chat_optimizer

        response, usage = chat_optimizer(
            system=system,
            user=user,
            max_completion_tokens=self.max_completion_tokens,
            retries=3,
            stage=stage,
            reasoning_effort=self.reasoning_effort,
        )
        parsed = extract_json(response)
        if not isinstance(parsed, dict) or not str(parsed.get("new_skill", "")).strip():
            raise GraphSkillGenerationError(
                f"{stage} response did not contain JSON object with a non-empty new_skill",
                prompt=user,
                raw_response=response,
                parsed=parsed if isinstance(parsed, dict) else {},
                usage=usage,
            )
        candidate = str(parsed["new_skill"]).rstrip() + "\n"
        try:
            if scope == "other":
                new_skill = adopt_other(parent_a, candidate)
            elif scope == "graph":
                new_skill = adopt_graph(parent_a, candidate)
            else:
                raise RuntimeError(f"unsupported operator scope: {scope}")
        except ValueError as exc:
            raise GraphSkillGenerationError(
                f"{stage} response did not contain a valid graph-structured skill: {exc}",
                prompt=user,
                raw_response=response,
                parsed=parsed,
                usage=usage,
                candidate=candidate,
            ) from exc
        if "notes" not in parsed or not isinstance(parsed["notes"], list):
            parsed["notes"] = []
        parsed["candidate_before_scope_enforcement"] = candidate
        parsed["scope_enforcement"] = scope
        return OperatorResult(
            new_skill=new_skill,
            prompt=user,
            raw_response=response,
            parsed=parsed,
            usage=usage,
        )

    def _build_mutation_prompt(
        self,
        *,
        scope: str,
        parent: str,
        context: str | dict | None,
    ) -> tuple[str, str]:
        system = load_prompt("mutation_other" if scope == "other" else "mutation_graph")
        task_guidance = load_default_mutation_task_guidance(self.env_name)
        if task_guidance:
            system = f"{system.rstrip()}\n\n## Task-Specific Mutation Guidance\n{task_guidance}\n"
        user = f"Environment: {self.env_name}\n\n## Parent Skill\n{parent}\n\n"
        reflection_context = _format_reflection_context(context)
        if reflection_context:
            user += f"## Reflection Context\n{reflection_context}\n\n"
        user += "Return JSON only with shape {\"new_skill\": \"...\", \"notes\": [\"...\"]}."
        return system, user
