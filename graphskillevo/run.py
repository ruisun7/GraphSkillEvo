#!/usr/bin/env python3
"""Standalone entry point for graphskillevo.

Usage:
    python -m graphskillevo.run --config configs/searchqa/default.yaml \
        --population_size 4 --generations 2
"""
from __future__ import annotations

import argparse
import os
import sys

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_PACKAGE_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _bool(text: str) -> bool:
    return str(text).lower() in {"true", "1", "yes", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="graphskillevo evolutionary skill optimization")
    parser.add_argument("--config", required=True, help="Path to existing GraphSkillEvo YAML config")
    parser.add_argument("--cfg-options", nargs="+", default=[], help="Override config values")
    parser.add_argument("--backend", type=str)
    parser.add_argument("--optimizer_model", type=str)
    parser.add_argument("--target_model", type=str)
    parser.add_argument("--optimizer_backend", type=str)
    parser.add_argument("--target_backend", type=str)
    parser.add_argument("--reasoning_effort", type=str)
    parser.add_argument("--skill_init", type=str)
    parser.add_argument("--out_root", type=str)
    parser.add_argument("--env", type=str)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--batch_size", type=int)
    parser.add_argument("--train_size", type=int)
    parser.add_argument("--population_size", type=int)
    parser.add_argument("--generations", type=int)
    parser.add_argument("--train_eval_num", type=int)
    parser.add_argument("--reflection_failure_k", type=int)
    parser.add_argument("--include_hidden_reference", type=_bool)
    parser.add_argument("--operator_max_completion_tokens", type=int)
    parser.add_argument("--operator_reasoning_effort", type=str)
    parser.add_argument("--initial_include_base_skill", type=_bool)
    parser.add_argument("--graph_retry_attempts", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from graphskillevo.adapters import get_adapter
    from graphskillevo.config import load_graphskillevo_config

    legacy = {
        key: value
        for key, value in vars(args).items()
        if key
        not in {
            "config",
            "cfg_options",
            "population_size",
            "generations",
            "train_eval_num",
            "reflection_failure_k",
            "include_hidden_reference",
            "operator_max_completion_tokens",
            "operator_reasoning_effort",
            "initial_include_base_skill",
            "graph_retry_attempts",
        }
        and value is not None
    }
    evolution_overrides = {}
    for key in (
        "population_size",
        "generations",
        "train_eval_num",
        "reflection_failure_k",
        "include_hidden_reference",
        "operator_max_completion_tokens",
        "operator_reasoning_effort",
        "initial_include_base_skill",
        "graph_retry_attempts",
    ):
        value = getattr(args, key, None)
        if value is not None:
            evolution_overrides[key] = value
    cfg, evolution_cfg = load_graphskillevo_config(
        args.config,
        cfg_options=list(args.cfg_options or []),
        legacy_overrides=legacy,
        evolution_overrides=evolution_overrides,
    )

    print("\n" + "=" * 60)
    print("  graphskillevo - Evolutionary Skill Optimization")
    print("=" * 60)
    print(f"  env:              {cfg.get('env')}")
    print(f"  optimizer_model:  {cfg.get('optimizer_model')}")
    print(f"  target_model:     {cfg.get('target_model')}")
    print(f"  population_size:  {evolution_cfg.population_size}")
    print(f"  generations:      {evolution_cfg.generations}")
    print(f"  out_root:         {cfg.get('out_root')}")
    print("=" * 60 + "\n")

    adapter = get_adapter(cfg)
    from graphskillevo.trainer import EvolutionarySkillTrainer

    trainer = EvolutionarySkillTrainer(cfg, evolution_cfg, adapter)
    summary = trainer.train()
    print(f"\n  Output saved to: {summary['out_root']}")
    best = summary.get("best", {})
    print(f"  Best skill: {best.get('id')} train_hard={best.get('train_hard')}")


if __name__ == "__main__":
    main()
