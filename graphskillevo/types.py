"""Typed records for the evolutionary method."""
from __future__ import annotations

from dataclasses import dataclass, field


def skill_hash(content: str) -> str:
    import hashlib

    return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass(slots=True)
class SkillIndividual:
    id: str
    content: str
    origin: str
    parent_ids: list[str] = field(default_factory=list)
    generation: int = 0
    train_hard: float | None = None
    train_soft: float | None = None
    val_hard: float | None = None
    val_soft: float | None = None
    survivor_score: float | None = None
    rank_score: float | None = None
    train_eval_dir: str = ""
    val_eval_dir: str = ""
    train_examples: list[dict] = field(default_factory=list)
    val_examples: list[dict] = field(default_factory=list)
    train_reflection_context: str = ""
    token_cumulative_run: dict = field(default_factory=dict)

    @property
    def hash(self) -> str:
        return skill_hash(self.content)

    def to_record(self) -> dict:
        return {
            "id": self.id,
            "origin": self.origin,
            "parent_ids": list(self.parent_ids),
            "generation": self.generation,
            "hash": self.hash,
            "skill_len": len(self.content),
            "train_hard": self.train_hard,
            "train_soft": self.train_soft,
            "val_hard": self.val_hard,
            "val_soft": self.val_soft,
            "rank_score": self.rank_score,
            "survivor_score": self.survivor_score,
            "train_eval_dir": self.train_eval_dir,
            "val_eval_dir": self.val_eval_dir,
            "train_examples": self.train_examples,
            "val_examples": self.val_examples,
            "train_reflection_context": self.train_reflection_context,
            "token_cumulative_run": self.token_cumulative_run,
        }
