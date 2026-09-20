"""Evolutionary skill optimization method for GraphSkillEvo benchmarks."""

__all__ = ["EvolutionarySkillTrainer"]


def __getattr__(name: str):
    if name == "EvolutionarySkillTrainer":
        from graphskillevo.trainer import EvolutionarySkillTrainer

        return EvolutionarySkillTrainer
    raise AttributeError(name)
