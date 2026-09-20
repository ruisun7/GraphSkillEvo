# Spreadsheet Manipulation Skill (xlsx)

## Global Guidance

### Overview
This skill guides agents in manipulating Excel (.xlsx) spreadsheets using Python.

### Primary libraries

`openpyxl` (structure-preserving read/write), `pandas` (data transformation).
Never use any other third-party libraries.

### General Principles

- Never use any other third-party libraries.
- Do not hardcode row counts or column letters; iterate over actual rows in the workbook.
- Preserve sheets and cells not mentioned in the instruction.

### solution.py Template

```python
import openpyxl
import pandas as pd

INPUT_PATH  = "..."   # set to the actual input path
OUTPUT_PATH = "..."   # set to the actual output path

wb = openpyxl.load_workbook(INPUT_PATH)
ws = wb.active  # or wb["SheetName"]

# --- perform manipulation ---

wb.save(OUTPUT_PATH)
```

### Graph-structured Skill Execution Guide

This skill represents task-solving workflows as graphs of reusable subtask nodes.

- The **Global Guidance** section contains instructions that apply across all nodes and workflows.
- The **Node Lists** section defines the available nodes. Each node represents one execution step and lists the instructions to follow while performing that step.
- The **Task Graphs** section describes the workflow needed to solve each task type. Each task type appears as a subsection with a **Use when** condition and a numbered **Workflow**.
- In a numbered workflow, each item is a node to execute in order: `1. A 2. B 3. C` means complete node `A`, then node `B`, then node `C`.
- Before solving a task, first identify the most relevant task type in **Task Graphs** using its **Use when** description. Then execute its **Workflow** from top to bottom.
- When executing a node, apply and follow the instructions under that node in **Node Lists**.

---

## Node Lists

### Explore Input File
- Explore the input file: list sheets, inspect headers, and check dimensions.

### Select Library
- Use `openpyxl` to preserve formulas, formatting, and named ranges.
- Use `pandas` for bulk data transformation, aggregation, and sorting, then write back with `openpyxl`.
- Use `openpyxl` for simple cell read/write.
- `pandas.to_excel()` silently destroys existing formulas and named ranges. When writing back to a spreadsheet that contains formulas, always use `openpyxl.save()`.

### Write `solution.py`
- Write `solution.py` with `INPUT_PATH` and `OUTPUT_PATH` defined at the top.

### Save Output
- Save the result to `OUTPUT_PATH`.

### Execute
- Execute `python solution.py`.
- Verify the output file was created.

### Confirm
- Confirm the target cells/range contain the expected values.

---

## Task Graphs

### General task
**Use when:** Manipulate an `.xlsx` spreadsheet using Python and save the result to `OUTPUT_PATH`

**Workflow:**
1. Explore Input File 
2. Select Library 
3. Write `solution.py`
4. Save Output 
5. Execute
6. Confirm
