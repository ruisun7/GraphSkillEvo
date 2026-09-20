"""Parent sampling and survivor selection helpers."""
from __future__ import annotations

import random

from graphskillevo.types import SkillIndividual


def normalized_rank_weights(population: list[SkillIndividual]) -> list[float]:
    n = len(population)
    if n <= 0:
        raise ValueError("population must not be empty")
    raw = [1.0 / (rank + n) for rank in range(n)]
    total = sum(raw)
    return [value / total for value in raw]


def sample_parent(population: list[SkillIndividual], rng: random.Random) -> SkillIndividual:
    weights = normalized_rank_weights(population)
    return rng.choices(population, weights=weights, k=1)[0]


def sorted_by_validation(population: list[SkillIndividual]) -> list[SkillIndividual]:
    return sorted(
        population,
        key=lambda item: (
            float(item.val_hard if item.val_hard is not None else -1.0),
            float(item.val_soft if item.val_soft is not None else -1.0),
        ),
        reverse=True,
    )


def select_survivors(
    parents: list[SkillIndividual],
    offspring: list[SkillIndividual],
    *,
    population_size: int,
) -> list[SkillIndividual]:
    combined: list[tuple[int, int, SkillIndividual]] = []
    for idx, item in enumerate(parents):
        combined.append((0, idx, item))
    for idx, item in enumerate(offspring):
        combined.append((1, idx, item))

    def key(row: tuple[int, int, SkillIndividual]) -> tuple[float, int, int]:
        group, idx, item = row
        score = item.val_hard
        return (
            float(score if score is not None else -1.0),
            -group,
            -idx,
        )

    survivors = [row[2] for row in sorted(combined, key=key, reverse=True)[:population_size]]
    for item in survivors:
        item.survivor_score = item.val_hard
    return survivors


def child_operator_sequence(population_size: int) -> list[str]:
    operators = ["mutation_other", "mutation_graph", "crossover_other", "crossover_graph"]
    return [operators[idx % len(operators)] for idx in range(population_size)]
