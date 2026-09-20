"""Evolutionary skill optimization trainer."""
from __future__ import annotations

import json
import os
import random
import time
from dataclasses import asdict

from graphskillevo.config import EvolutionConfig
from graphskillevo.evaluation import SkillEvaluator
from graphskillevo.graph_skill import assert_graph_skill
from graphskillevo.operators import EvolutionOperators, GraphSkillGenerationError
from graphskillevo.selection import (
    child_operator_sequence,
    normalized_rank_weights,
    sample_parent,
    select_survivors,
    sorted_by_validation,
)
from graphskillevo.task_context import build_initial_task_context
from graphskillevo.types import SkillIndividual
from graphskillevo.utils import read_text_if_exists, redact_cfg, token_delta, write_json, write_text


def configure_models(cfg: dict) -> None:
    from graphskillevo.model_setup import configure_models as _configure_models

    _configure_models(cfg)


def _get_token_summary() -> dict:
    try:
        from graphskillevo.model import get_token_summary

        return get_token_summary()
    except ModuleNotFoundError:
        return {"_total": {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


def _reset_token_tracker() -> None:
    try:
        from graphskillevo.model import reset_token_tracker

        reset_token_tracker()
    except ModuleNotFoundError:
        return


class EvolutionarySkillTrainer:
    def __init__(
        self,
        cfg: dict,
        evolution_cfg: EvolutionConfig,
        adapter,
        *,
        operators: EvolutionOperators | None = None,
    ) -> None:
        self.cfg = cfg
        self.evolution_cfg = evolution_cfg
        self.adapter = adapter
        self.operators = operators
        self.history: list[dict] = []
        self.validation_cache: dict[str, dict] = {}
        self.assert_graph_skill_failure_count = 0

    def train(self) -> dict:
        cfg = self.cfg
        evolution = self.evolution_cfg
        out_root = cfg["out_root"]
        os.makedirs(out_root, exist_ok=True)
        self._load_validation_cache()
        _reset_token_tracker()
        write_json(
            os.path.join(out_root, "config.json"),
            {"graphskillevo": redact_cfg(cfg), "evolution": asdict(evolution)},
        )

        configure_models(cfg)
        self.adapter.setup(cfg)
        dataloader = self.adapter.get_dataloader()
        evaluator = SkillEvaluator(self.adapter, dataloader, out_root, int(cfg.get("seed", 42)))
        operators = self.operators or EvolutionOperators(
            env_name=str(cfg.get("env", "")),
            max_completion_tokens=evolution.operator_max_completion_tokens,
            reasoning_effort=evolution.operator_reasoning_effort,
            graph_retry_attempts=evolution.graph_retry_attempts,
        )

        print(
            f"  [graphskillevo] population={evolution.population_size} generations={evolution.generations} "
            "selection=valid_seen"
        )

        t0 = time.time()
        population = self._initialize_population(operators)
        self._evaluate_population(
            evaluator,
            population,
            generation=0,
            evaluate_train=False,
            evaluate_validation=True,
        )
        self._save_population(population, generation=0)
        best = self._best_individual(population)
        write_text(os.path.join(out_root, "best_skill.md"), best.content)
        self._save_runtime_state(generation=0, population=population, best=best)

        for generation in range(1, evolution.generations + 1):
            gen_t0 = time.time()
            print(f"\n  [GENERATION {generation}/{evolution.generations}]")
            self._evaluate_population(
                evaluator,
                population,
                generation=generation,
                evaluate_train=True,
                evaluate_validation=False,
            )
            ranked_for_parents = sorted_by_validation(population)
            weights = normalized_rank_weights(ranked_for_parents)
            offspring, operator_records = self._generate_offspring(
                operators,
                ranked_for_parents,
                weights,
                generation=generation,
            )
            generation_assert_graph_failures = sum(
                int(record.get("assert_graph_skill_failure_count", 0) or 0)
                for record in operator_records
            )
            self._evaluate_population(
                evaluator,
                offspring,
                generation=generation,
                evaluate_train=False,
                evaluate_validation=True,
            )
            next_population = select_survivors(
                population,
                offspring,
                population_size=evolution.population_size,
            )
            next_population = sorted(
                next_population,
                key=lambda item: float(item.survivor_score if item.survivor_score is not None else -1.0),
                reverse=True,
            )
            best = self._best_individual(next_population)
            population_record = {
                "generation": generation,
                "parent_population": [item.to_record() for item in population],
                "ranked_for_parent_selection": [
                    {**item.to_record(), "selection_weight": weights[idx]}
                    for idx, item in enumerate(ranked_for_parents)
                ],
                "offspring": [item.to_record() for item in offspring],
                "operator_records": operator_records,
                "assert_graph_skill_failure_count": generation_assert_graph_failures,
                "next_population": [item.to_record() for item in next_population],
                "best": best.to_record(),
                "wall_time_s": round(time.time() - gen_t0, 1),
            }
            gen_dir = os.path.join(out_root, "generations", f"generation_{generation:04d}")
            write_json(os.path.join(gen_dir, "generation_record.json"), population_record)
            self.history.append(population_record)
            write_json(os.path.join(out_root, "history.json"), self.history)
            population = next_population
            self._save_population(population, generation=generation)
            write_text(os.path.join(out_root, "best_skill.md"), best.content)
            self._save_runtime_state(generation=generation, population=population, best=best)
            best_train = f"{best.train_hard:.4f}" if best.train_hard is not None else "None"
            best_val = f"{best.val_hard:.4f}" if best.val_hard is not None else "None"
            print(
                f"  [GENERATION {generation} done] "
                f"best train_hard={best_train} "
                f"val_hard={best_val}"
            )

        summary = {
            "out_root": out_root,
            "population_size": evolution.population_size,
            "generations": evolution.generations,
            "best": self._best_individual(population).to_record(),
            "wall_time_s": round(time.time() - t0, 1),
            "assert_graph_skill_failure_count": self.assert_graph_skill_failure_count,
            "tokens": _get_token_summary(),
        }
        write_json(os.path.join(out_root, "summary.json"), summary)
        return summary

    def _initialize_population(self, operators: EvolutionOperators) -> list[SkillIndividual]:
        evolution = self.evolution_cfg
        cfg = self.cfg
        base_skill = ""
        skill_init_path = os.path.abspath(str(cfg.get("skill_init") or ""))
        if evolution.initial_include_base_skill and skill_init_path:
            base_skill = read_text_if_exists(skill_init_path)

        population: list[SkillIndividual] = []
        if base_skill:
            assert_graph_skill(base_skill)
            population.append(
                SkillIndividual(
                    id="g0000_i0000",
                    content=base_skill.rstrip() + "\n",
                    origin="initial_skill",
                    generation=0,
                )
            )
            print(f"  [initial skill] included {skill_init_path} ({len(base_skill)} chars)")
        else:
            print("  [initial skill] missing or disabled; full population will be LLM-generated")

        needed = evolution.population_size - len(population)
        init_dir = os.path.join(cfg["out_root"], "initialization")
        if needed > 0:
            try:
                skills, init_record = operators.initialize_population(
                    n=needed,
                    base_skill=base_skill,
                    task_context=build_initial_task_context(cfg),
                )
                self.assert_graph_skill_failure_count += int(
                    init_record.get("assert_graph_skill_failure_count", 0) or 0
                )
                write_json(os.path.join(init_dir, "init_population_result.json"), init_record)
            except Exception as exc:
                write_json(os.path.join(init_dir, "init_population_error.json"), {"error": str(exc), "needed": needed})
                raise
            start_idx = len(population)
            for offset, skill in enumerate(skills):
                assert_graph_skill(skill)
                population.append(
                    SkillIndividual(
                        id=f"g0000_i{start_idx + offset:04d}",
                        content=skill,
                        origin="llm_initialization",
                        generation=0,
                    )
                )
        return population

    def _evaluate_population(
        self,
        evaluator: SkillEvaluator,
        population: list[SkillIndividual],
        *,
        generation: int,
        evaluate_train: bool = True,
        evaluate_validation: bool = True,
    ) -> None:
        evolution = self.evolution_cfg
        train_eval_seed = int(self.cfg.get("seed", 42)) + generation * 10000
        for individual in population:
            item_dir = os.path.join(
                self.cfg["out_root"],
                "generations",
                f"generation_{generation:04d}",
                "evaluations",
                individual.id,
            )

            if evaluate_train:
                result = evaluator.evaluate(
                    skill_content=individual.content,
                    split="train",
                    env_num=evolution.train_eval_num,
                    seed=train_eval_seed,
                    out_dir=os.path.join(item_dir, "eval_train"),
                    reflection_failure_k=evolution.reflection_failure_k,
                    include_hidden_reference=evolution.include_hidden_reference,
                )
                individual.train_hard = result.hard
                individual.train_soft = result.soft
                individual.train_eval_dir = result.out_dir
                individual.train_examples = result.examples
                individual.train_reflection_context = result.reflection_context
                write_json(os.path.join(item_dir, "train_score.json"), result.to_record())

            cached_record = None
            if evaluate_validation:
                val_key = self._validation_cache_key(individual)
                cached_record = self.validation_cache.get(val_key)
                if cached_record is not None:
                    self._assign_validation_record(individual, cached_record)
                    val_record = dict(cached_record)
                    val_record["cached"] = True
                else:
                    result = evaluator.evaluate(
                        skill_content=individual.content,
                        split="valid_seen",
                        env_num=0,
                        seed=int(self.cfg.get("seed", 42)),
                        out_dir=os.path.join(item_dir, "eval_val"),
                        reflection_failure_k=0,
                    )
                    val_record = {
                        **result.to_record(),
                        "hash": individual.hash,
                        "split": "valid_seen",
                        "skill_len": len(individual.content),
                        "cached": False,
                    }
                    self.validation_cache[val_key] = val_record
                    self._save_validation_cache()
                    self._assign_validation_record(individual, val_record)
                token_cumulative_run = _get_token_summary()
                individual.token_cumulative_run = token_cumulative_run
                val_record["token_cumulative_run"] = token_cumulative_run
                write_json(os.path.join(item_dir, "val_score.json"), val_record)

                individual.rank_score = individual.val_hard
                individual.survivor_score = individual.val_hard

            train_score = f"{individual.train_hard:.4f}" if individual.train_hard is not None else "None"
            val_score = f"{individual.val_hard:.4f}" if individual.val_hard is not None else "None"
            print(
                f"    [eval] {individual.id} train_hard={train_score}"
                f" val_hard={val_score}"
                + (" cached_val=true" if cached_record is not None else "")
            )

    def _validation_cache_path(self) -> str:
        return os.path.join(self.cfg["out_root"], "evaluation_cache.json")

    def _load_validation_cache(self) -> None:
        path = self._validation_cache_path()
        if not os.path.isfile(path):
            self.validation_cache = {}
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.validation_cache = {}
            return
        self.validation_cache = data if isinstance(data, dict) else {}

    def _save_validation_cache(self) -> None:
        write_json(self._validation_cache_path(), self.validation_cache)

    @staticmethod
    def _validation_cache_key(individual: SkillIndividual) -> str:
        return f"{individual.hash}:valid_seen"

    @staticmethod
    def _assign_validation_record(individual: SkillIndividual, record: dict) -> None:
        individual.val_hard = float(record.get("hard", 0.0) or 0.0)
        individual.val_soft = float(record.get("soft", 0.0) or 0.0)
        individual.val_eval_dir = str(record.get("out_dir") or "")
        examples = record.get("examples") or []
        individual.val_examples = list(examples) if isinstance(examples, list) else []

    def _generate_offspring(
        self,
        operators: EvolutionOperators,
        ranked_population: list[SkillIndividual],
        weights: list[float],
        *,
        generation: int,
    ) -> tuple[list[SkillIndividual], list[dict]]:
        rng = random.Random(int(self.cfg.get("seed", 42)) + generation * 3000)
        offspring: list[SkillIndividual] = []
        records: list[dict] = []
        operator_sequence = child_operator_sequence(self.evolution_cfg.population_size)
        for child_idx, operator_name in enumerate(operator_sequence):
            child_id = f"g{generation:04d}_i{child_idx:04d}"
            child_dir = os.path.join(
                self.cfg["out_root"],
                "generations",
                f"generation_{generation:04d}",
                "offspring",
                child_id,
            )
            os.makedirs(child_dir, exist_ok=True)
            retry_records: list[dict] = []
            assert_graph_skill_failure_count = 0
            parent_resample_count = 0
            graph_retry_attempts = max(1, int(self.evolution_cfg.graph_retry_attempts))

            while True:
                parent_ids, parent_payload, context = self._sample_operator_inputs(
                    operator_name,
                    ranked_population,
                    weights,
                    rng,
                )
                for attempt_in_parent_sample in range(1, graph_retry_attempts + 1):
                    tokens_before = _get_token_summary()
                    try:
                        result = self._invoke_operator(
                            operators,
                            operator_name,
                            parent_payload,
                            context,
                        )
                    except GraphSkillGenerationError as exc:
                        tokens_after = _get_token_summary()
                        retry_records.append(
                            self._failed_attempt_record(
                                retry_index=len(retry_records) + 1,
                                attempt_in_parent_sample=attempt_in_parent_sample,
                                parent_resample_count=parent_resample_count,
                                operator_name=operator_name,
                                parent_ids=parent_ids,
                                context=context,
                                error_record=exc.to_record(),
                                tokens=token_delta(tokens_before, tokens_after),
                            )
                        )
                        print(
                            f"    [operator retry] {operator_name} -> {child_id} "
                            f"parents={parent_ids} attempt={attempt_in_parent_sample}/{graph_retry_attempts} "
                            f"error={exc}"
                        )
                        continue

                    tokens_after = _get_token_summary()
                    try:
                        assert_graph_skill(result.new_skill)
                    except ValueError as exc:
                        assert_graph_skill_failure_count += 1
                        self.assert_graph_skill_failure_count += 1
                        retry_records.append(
                            self._failed_attempt_record(
                                retry_index=len(retry_records) + 1,
                                attempt_in_parent_sample=attempt_in_parent_sample,
                                parent_resample_count=parent_resample_count,
                                operator_name=operator_name,
                                parent_ids=parent_ids,
                                context=context,
                                error_record={
                                    "failure_type": "assert_graph_skill",
                                    "error": f"operator returned non-graph skill: {exc}",
                                    "prompt": result.prompt,
                                    "raw_response": result.raw_response,
                                    "parsed": result.parsed,
                                    "usage": result.usage,
                                    "candidate": result.new_skill,
                                },
                                tokens=token_delta(tokens_before, tokens_after),
                            )
                        )
                        print(
                            f"    [operator retry] assert_graph_skill failed for {operator_name} -> {child_id} "
                            f"parents={parent_ids} attempt={attempt_in_parent_sample}/{graph_retry_attempts} "
                            f"error={exc}; regenerating"
                        )
                        continue
                    break
                else:
                    parent_resample_count += 1
                    print(
                        f"    [operator retry] {operator_name} -> {child_id} "
                        f"resampling parents after {graph_retry_attempts} invalid attempts"
                    )
                    continue
                break

            child = SkillIndividual(
                id=child_id,
                content=result.new_skill,
                origin=operator_name,
                parent_ids=parent_ids,
                generation=generation,
            )
            offspring.append(child)
            write_text(os.path.join(child_dir, "candidate_skill.md"), result.new_skill)
            record = {
                "child_id": child_id,
                "operator": operator_name,
                "parent_ids": parent_ids,
                "rank_weights": context["rank_weights"],
                "selected_parents": context["selected_parents"],
                "prompt": result.prompt,
                "raw_response": result.raw_response,
                "parsed": result.parsed,
                "usage": result.usage,
                "tokens": token_delta(tokens_before, tokens_after),
                "retry_attempts": retry_records,
                "retry_count": len(retry_records),
                "assert_graph_skill_failure_count": assert_graph_skill_failure_count,
                "parent_resample_count": parent_resample_count,
            }
            write_json(os.path.join(child_dir, "operator_record.json"), record)
            records.append(record)
            print(f"    [operator] {operator_name} -> {child_id} parents={parent_ids}")
        return offspring, records

    def _sample_operator_inputs(
        self,
        operator_name: str,
        ranked_population: list[SkillIndividual],
        weights: list[float],
        rng: random.Random,
    ) -> tuple[list[str], dict, dict]:
        if operator_name in {"crossover_other", "crossover_graph"}:
            parent_a = sample_parent(ranked_population, rng)
            parent_b = sample_parent(ranked_population, rng)
            parent_ids = [parent_a.id, parent_b.id]
            context = self._operator_context(ranked_population, weights, parent_ids, include_reflection=False)
            return parent_ids, {"parent_a": parent_a.content, "parent_b": parent_b.content}, context
        if operator_name in {"mutation_other", "mutation_graph"}:
            parent = sample_parent(ranked_population, rng)
            parent_ids = [parent.id]
            context = self._operator_context(ranked_population, weights, parent_ids, include_reflection=False)
            return (
                parent_ids,
                {
                    "parent": parent.content,
                    "reflection_context": parent.train_reflection_context,
                },
                context,
            )
        raise ValueError(f"Unknown operator: {operator_name}")

    def _invoke_operator(
        self,
        operators: EvolutionOperators,
        operator_name: str,
        parent_payload: dict,
        context: dict,
    ):
        if operator_name == "crossover_other":
            return operators.crossover_other(
                parent_a=parent_payload["parent_a"],
                parent_b=parent_payload["parent_b"],
                context=None,
            )
        if operator_name == "crossover_graph":
            return operators.crossover_graph(
                parent_a=parent_payload["parent_a"],
                parent_b=parent_payload["parent_b"],
                context=None,
            )
        if operator_name == "mutation_other":
            return operators.mutation_other(
                parent=parent_payload["parent"],
                context=parent_payload.get("reflection_context") or None,
            )
        if operator_name == "mutation_graph":
            return operators.mutation_graph(
                parent=parent_payload["parent"],
                context=parent_payload.get("reflection_context") or None,
            )
        raise ValueError(f"Unknown operator: {operator_name}")

    def _failed_attempt_record(
        self,
        *,
        retry_index: int,
        attempt_in_parent_sample: int,
        parent_resample_count: int,
        operator_name: str,
        parent_ids: list[str],
        context: dict,
        error_record: dict,
        tokens: dict,
    ) -> dict:
        return {
            "retry_index": retry_index,
            "attempt_in_parent_sample": attempt_in_parent_sample,
            "parent_resample_count": parent_resample_count,
            "operator": operator_name,
            "parent_ids": parent_ids,
            "selected_parents": context["selected_parents"],
            "failure_type": error_record.get("failure_type", ""),
            "error": error_record.get("error", ""),
            "prompt": error_record.get("prompt", ""),
            "raw_response": error_record.get("raw_response", ""),
            "parsed": error_record.get("parsed", {}),
            "usage": error_record.get("usage", {}),
            "candidate": error_record.get("candidate", ""),
            "tokens": tokens,
        }

    def _individual_context(self, item: SkillIndividual, *, include_reflection: bool) -> dict:
        context = {
            "id": item.id,
            "origin": item.origin,
            "hash": item.hash,
            "train_hard": item.train_hard,
            "train_soft": item.train_soft,
            "val_hard": item.val_hard,
            "val_soft": item.val_soft,
            "train_eval_dir": item.train_eval_dir,
            "val_eval_dir": item.val_eval_dir,
            "val_examples": [],
        }
        if include_reflection:
            context["train_reflection_context"] = item.train_reflection_context
        return context

    def _operator_context(
        self,
        ranked_population: list[SkillIndividual],
        weights: list[float],
        parent_ids: list[str],
        *,
        include_reflection: bool,
    ) -> dict:
        by_id = {item.id: item for item in ranked_population}
        return {
            "selected_parent_ids": parent_ids,
            "selected_parents": [
                self._individual_context(by_id[parent_id], include_reflection=include_reflection)
                for parent_id in parent_ids
                if parent_id in by_id
            ],
            "rank_weights": [
                {
                    "id": item.id,
                    "rank": idx,
                    "weight": weights[idx],
                    "train_hard": item.train_hard,
                    "train_soft": item.train_soft,
                    "val_hard": item.val_hard,
                    "val_soft": item.val_soft,
                    "origin": item.origin,
                }
                for idx, item in enumerate(ranked_population)
            ],
        }

    def _save_population(self, population: list[SkillIndividual], *, generation: int) -> None:
        pop_dir = os.path.join(self.cfg["out_root"], "population", f"generation_{generation:04d}")
        for idx, individual in enumerate(population):
            write_text(os.path.join(pop_dir, f"{idx:04d}_{individual.id}.md"), individual.content)
        write_json(os.path.join(pop_dir, "population.json"), [item.to_record() for item in population])

    def _save_runtime_state(
        self,
        *,
        generation: int,
        population: list[SkillIndividual],
        best: SkillIndividual,
    ) -> None:
        write_json(
            os.path.join(self.cfg["out_root"], "runtime_state.json"),
            {
                "last_completed_generation": generation,
                "population": [item.to_record() for item in population],
                "best": best.to_record(),
                "best_skill_path": os.path.join(self.cfg["out_root"], "best_skill.md"),
            },
        )

    def _best_individual(self, population: list[SkillIndividual]) -> SkillIndividual:
        return max(population, key=lambda item: float(item.val_hard if item.val_hard is not None else -1.0))
