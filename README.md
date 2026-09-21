# GraphSkillEvo

Code for the paper **GRAPHSKILLEVO: EVOLUTIONARY OPTIMIZATION OF GRAPH-STRUCTURED AGENT SKILLS** [Arxiv](https://arxiv.org/abs/2609.21749).

## Install

GraphSkillEvo requires Python 3.10+.

```bash
pip install -e .

# For the ALFWorld benchmark (optional):
pip install -e ".[alfworld]"
alfworld-download
```

Configure model access before launching runs. For OpenAI-compatible APIs:

```bash
export AZURE_OPENAI_ENDPOINT="https://api.openai.com/v1"
export AZURE_OPENAI_API_KEY="sk-..."
export AZURE_OPENAI_AUTH_MODE="openai_compatible"
```

## Data Preparation

See [data/README.md](data/README.md) for the complete data layout. The
repository releases lightweight split manifests under `data/`; large benchmark
payloads should be downloaded or materialized separately before optimization or
evaluation.

| Benchmark | Config | Released split manifest | Runnable data path |
|---|---|---|---|
| ALFWorld | `configs/alfworld/default.yaml` | `data/alfworld_path_split` | `data/alfworld_path_split` plus the ALFWorld data root |
| DocVQA | `configs/docvqa/default.yaml` | `data/docvqa_id_split` | `data/docvqa/splits` and `data/docvqa_images` |
| LiveMathematicianBench | `configs/livemathematicianbench/default.yaml` | `data/livemathematicianbench_id_split` | `data/livemathematicianbench_split` |
| SearchQA | `configs/searchqa/default.yaml` | `data/searchqa_id_split` | `data/searchqa_split` |
| SpreadsheetBench | `configs/spreadsheetbench/default.yaml` | `data/spreadsheetbench_id_split` | `data/spreadsheetbench_split` and `data/spreadsheetbench_verified_400` |

ALFWorld requires the optional dependency and raw data downloaded by
`alfworld-download`.

## Skill Optimization

DocVQA:

```bash
python -m graphskillevo.run \
  --config configs/docvqa/default.yaml \
  --out_root outputs/graphskillevo/docvqa
```

SearchQA:

```bash
python -m graphskillevo.run \
  --config configs/searchqa/default.yaml \
  --out_root outputs/graphskillevo/searchqa
```

LiveMathematicianBench:

```bash
python -m graphskillevo.run \
  --config configs/livemathematicianbench/default.yaml \
  --out_root outputs/graphskillevo/livemathematicianbench
```

SpreadsheetBench:

```bash
python -m graphskillevo.run \
  --config configs/spreadsheetbench/default.yaml \
  --out_root outputs/graphskillevo/spreadsheetbench
```

ALFWorld:

```bash
python -m graphskillevo.run \
  --config configs/alfworld/default.yaml \
  --out_root outputs/graphskillevo/alfworld
```

Each run writes evolved populations, logs, summaries, and the selected skill
artifact under its `--out_root`.

## Evaluation

Use `scripts/eval_only.py` to evaluate a saved skill without re-running
optimization. Replace `path/to/best_skill.md` with the skill artifact you want
to test.

SearchQA:

```bash
python scripts/eval_only.py \
  --split valid_unseen \
  --target_model gpt-5.4-nano \
  --target_backend openai_chat \
  --reasoning_effort medium \
  --config configs/searchqa/default.yaml \
  --split_dir data/searchqa_split \
  --skill path/to/best_skill.md \
  --out_root outputs/eval/searchqa
```

DocVQA:

```bash
python scripts/eval_only.py \
  --split valid_unseen \
  --target_model gpt-5.4-nano \
  --target_backend openai_chat \
  --reasoning_effort medium \
  --config configs/docvqa/default.yaml \
  --split_dir data/docvqa/splits \
  --workers 4 \
  --skill path/to/best_skill.md \
  --out_root outputs/eval/docvqa
```

LiveMathematicianBench:

```bash
python scripts/eval_only.py \
  --split valid_unseen \
  --target_model gpt-5.4-nano \
  --target_backend openai_chat \
  --reasoning_effort medium \
  --config configs/livemathematicianbench/default.yaml \
  --split_dir data/livemathematicianbench_split \
  --skill path/to/best_skill.md \
  --out_root outputs/eval/livemathematicianbench
```

SpreadsheetBench:

```bash
python scripts/eval_only.py \
  --split valid_unseen \
  --target_model gpt-5.4-nano \
  --target_backend openai_chat \
  --reasoning_effort medium \
  --config configs/spreadsheetbench/default.yaml \
  --split_dir data/spreadsheetbench_split \
  --data_root data/spreadsheetbench_verified_400 \
  --workers 4 \
  --skill path/to/best_skill.md \
  --out_root outputs/eval/spreadsheetbench
```

ALFWorld:

```bash
python scripts/eval_only.py \
  --split valid_unseen \
  --target_model gpt-5.4-nano \
  --target_backend openai_chat \
  --reasoning_effort medium \
  --config configs/alfworld/default.yaml \
  --split_dir data/alfworld_path_split \
  --skill path/to/best_skill.md \
  --out_root outputs/eval/alfworld
```

The evaluation script reports hard and soft scores and writes
`eval_summary.json` to the output directory.

## Pretrained Skill Artifacts

Pretrained GraphSkillEvo skills are plain Markdown files released under
`ckpt/`. They can be passed directly to `scripts/eval_only.py` with `--skill`.

```text
ckpt/gpt-5.4-nano/
|-- alfworld/best_skill.md
|-- docvqa/best_skill.md
|-- livemath/best_skill.md
|-- searchqa/best_skill.md
|-- spreadsheetbench/best_skill.md
```
## Citation

If you use this code or the released skill artifacts, please cite the
corresponding paper:

```bibtex
@misc{sun2026graphskillevoevolutionaryoptimizationgraphstructured,
      title={GraphSkillEvo: Evolutionary Optimization of Graph-Structured Agent Skills}, 
      author={Rui Sun and Zhi Zheng and Zhenkun Wang and Zhichao Lu},
      year={2026},
      eprint={2609.21749},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2609.21749}, 
}
```
