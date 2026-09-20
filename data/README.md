# Data Manifests

This directory releases lightweight split manifests for the GraphSkillEvo paper
splits. These manifests are not full runnable benchmark payloads. To evaluate a
benchmark, first materialize the full examples from the raw data source when
needed, then point `--split_dir` at the split directory listed below.

In this README, "coverage" describes which part of the upstream benchmark the
manifest references. It does not mean the released manifest directory contains
the full runnable examples.

## Layout

Every released manifest directory uses the same file layout:

```text
data/<benchmark>_<manifest_type>/
|-- split_manifest.json
|-- train/items.json
|-- val/items.json
`-- test/items.json
```

`split_manifest.json` records source metadata, split counts, and item fields.
Each `items.json` contains only stable IDs or source-path hints.

DocVQA is materialized into CSV split files for the runnable environment:

```text
data/docvqa/splits/
|-- split_manifest.json
|-- train/train.csv
|-- val/val.csv
`-- test/test.csv
```

## Released Splits

| Manifest directory | Benchmark | Counts | Coverage | Raw data source | `split_dir` |
|---|---|---:|---|---|---|
| `searchqa_id_split/` | SearchQA | 400 / 200 / 1400 | Official HF dataset IDs | [lucadiliello/searchqa](https://huggingface.co/datasets/lucadiliello/searchqa) | `data/searchqa_split` |
| `livemathematicianbench_id_split/` | LiveMathematicianBench | 35 / 18 / 124 | Four official monthly files | [LiveMathematicianBench/LiveMathematicianBench](https://huggingface.co/datasets/LiveMathematicianBench/LiveMathematicianBench) | `data/livemathematicianbench_split` |
| `docvqa_id_split/` | DocVQA | 107 / 53 / 374 | 10% subset of validation | [lmms-lab/DocVQA](https://huggingface.co/datasets/lmms-lab/DocVQA) | `data/docvqa/splits` |
| `spreadsheetbench_id_split/` | SpreadsheetBench | 80 / 40 / 280 | SpreadsheetBench Verified 400 | [KAKA22/SpreadsheetBench](https://huggingface.co/datasets/KAKA22/SpreadsheetBench) | `data/spreadsheetbench_split` |
| `alfworld_path_split/` | ALFWorld | 39 / 18 / 134 | ALFWorld `json_2.1.1` paths | [alfworld/alfworld](https://github.com/alfworld/alfworld) | `data/alfworld_path_split` |

Counts are ordered as train / val / test.

## Direct Use

Only `alfworld_path_split/` can be used directly as `--split_dir` from the
released manifest directories, because the ALFWorld loader reads `gamefile` and
`task_type` from the split items.

This does not mean the ALFWorld raw data is included. You still need to
download ALFWorld separately with `alfworld-download` and set `$ALFWORLD_DATA`
or the configured ALFWorld data root to a directory containing `json_2.1.1`.

The other manifest directories are lookup manifests. They intentionally omit
full example fields such as questions, answers, contexts, images, or task
instructions. Materialize those benchmarks into the `split_dir` paths listed
above before running GraphSkillEvo.

If this checkout already contains a materialized split directory, treat the
corresponding `*_id_split/` directory as the stable recipe for rebuilding it
from the upstream source.

## Lookup Keys

The manifests are sufficient to locate the corresponding raw examples after
the raw data has been downloaded or otherwise made available:

| Benchmark | Manifest lookup key |
|---|---|
| SearchQA | Match `items.json[].id` to the `key` field in `lucadiliello/searchqa`. |
| LiveMathematicianBench | Open `source_file`, then match `no`; the manifest `id` is `<month>:<no>`. |
| DocVQA | Match `questionId` within the official DocVQA `validation` split; `image_path` records the expected local image path. |
| SpreadsheetBench | Match `id`; `spreadsheet_path` identifies the referenced spreadsheet directory. |
| ALFWorld | Resolve `gamefile` relative to the ALFWorld data root. |

## Manifest Item Examples

SearchQA:

```json
{
  "id": "221c83e6630f4e7983da48fa28da1882"
}
```

LiveMathematicianBench:

```json
{
  "id": "202602:22",
  "month": "202602",
  "no": 22,
  "paper_link": "http://arxiv.org/abs/2602.10700v1",
  "source_file": "data/202602/qa_202602_final.json"
}
```

DocVQA:

```json
{
  "id": "50877",
  "questionId": "50877",
  "docId": "14724",
  "image_path": "data/docvqa_images/q50877_d14724.png",
  "source_split": "validation"
}
```

SpreadsheetBench:

```json
{
  "id": "32438",
  "spreadsheet_path": "spreadsheet/32438",
  "instruction_type": "Cell-Level Manipulation"
}
```

ALFWorld:

```json
{
  "id": "train:0000",
  "gamefile": "json_2.1.1/train/.../game.tw-pddl",
  "task_type": "look_at_obj_in_light"
}
```

## Benchmark Notes

### SearchQA

`searchqa_id_split/` is an ID-only manifest. Each released `id` exactly matches
the `key` field in `lucadiliello/searchqa`.

Materialized examples must include the fields consumed by the SearchQA
environment, including:

```text
id
question
context
answers
```

Write the full examples to:

```text
data/searchqa_split
```

### LiveMathematicianBench

`livemathematicianbench_id_split/` was generated from these raw files:

```text
data/202511/qa_202511_final.json
data/202512/qa_202512_final.json
data/202601/qa_202601_final.json
data/202602/qa_202602_final.json
```

The manifest stores IDs in the loader format:

```text
<month>:<no>
```

Materialized examples must include:

```text
question
choices
correct_choice
theorem_type
theorem
sketch
paper_link
```

Write the full examples to:

```text
data/livemathematicianbench_split
```

### DocVQA

`docvqa_id_split/` records `docvqa_validation_10pct`: a 10% subset sampled from
the official DocVQA `validation` split.

```text
source_split: validation
docvqa_validation_10pct: train=107, val=53, test=374
```

Each manifest item contains question/document IDs plus image location metadata.
Materialized examples must provide `question`, `answer` or `ground_truth`, and
an `image_path` that resolves locally.

Write the runnable CSV splits and images to:

```text
data/docvqa/splits
data/docvqa_images
```

### SpreadsheetBench

`spreadsheetbench_id_split/` records the split over SpreadsheetBench Verified
400, from `spreadsheetbench_verified_400.tar.gz`.

Each manifest item contains task identity metadata such as `id`,
`spreadsheet_path`, and `instruction_type`. Materialization must also place the
referenced spreadsheet directories at:

```text
data/spreadsheetbench_verified_400
```

Write the runnable task metadata to:

```text
data/spreadsheetbench_split
```

### ALFWorld

`alfworld_path_split/` records `gamefile` paths relative to the ALFWorld data
root. The source payload is `json_2.1.1`, which must be downloaded separately
with `alfworld-download`.

Install the ALFWorld extra and download the raw data before running:

```bash
python3.10 -m pip install -e ".[alfworld]"
alfworld-download
```

This manifest can be used directly as `--split_dir` after the ALFWorld data root
points to a local directory containing `json_2.1.1`.

## Regenerating Materialized Splits

To rebuild a runnable split from upstream data, use the corresponding
`*_id_split/` manifest as the stable selection list, then write the full
examples into the runnable path expected by the config. Keep the split names
`train`, `val`, and `test`; GraphSkillEvo maps them internally to training,
validation-seen, and validation-unseen evaluation splits.
