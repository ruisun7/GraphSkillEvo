# DocVQA Skill: Table and Cell-Level Question Answering

## Global Guidance

### Overview
This skill targets questions whose answers live inside tables (rows/columns) or require selecting a specific cell using nearby headers/row labels.

### General Principles
- Answer only using the table cell contents that are visually present.
- Use table structure: column headers, row labels, and section dividers.
- Prefer extracting a single exact cell span; avoid paraphrasing.
- If the question references a specific row entity, match that entity first, then take the intersecting cell under the correct column.
- When multiple tables exist, choose the table whose headers/context best match the question.

### Graph-structured Skill Execution Guide
- Pick the most relevant task graph under **Task Graphs**.
- Execute the workflow nodes sequentially.
- Each node’s instructions under **Node Lists** define exactly what to do.

## Node Lists

### Identify Relevant Table and Axes
- Locate all visible tables in the document.
- Determine which table is relevant by matching question keywords to table headers or surrounding captions.
- Identify the “row axis” (row headers/leftmost labels) and the “column axis” (top headers).

### Extract Row Key (If Applicable)
- If the question mentions an entity (person/item/account/product), find the row where that entity appears.
- Capture the exact row label text as evidence.

### Extract Column Key (If Applicable)
- If the question asks for a field/attribute, find the column header that matches.
- Capture the exact column header text as evidence.

### Locate Intersecting Cell Span
- Move to the cell at the intersection of the selected row and column.
- If the table uses grouped headers (multi-row headers), ensure you use the correct full header path.
- Extract the smallest exact text span within that cell that answers the question.

### Handle Merged/Spanning Cells
- If cells are merged/spanning, ensure the extraction comes from the region that corresponds to the requested header/row.
- Use visual boundaries (thick borders, merged area extents) to avoid adjacent incorrect values.

### Validate Table Evidence
- Verify the row label and column header match the question constraints.
- Confirm the extracted value is directly inside the correct cell.

### Format Final Answer Tag
- Output the final extracted value inside `<answer>...</answer>`.
- If no matching row/column intersection is visible, output “not visible in document” (or equivalent) without guessing.

## Task Graphs

### Table Cell Retrieval
**Use when:** The question asks for a value from a table, or clearly requires selecting a cell using row/column headers.

**Workflow:**
1. Identify Relevant Table and Axes
2. Extract Row Key (If Applicable)
3. Extract Column Key (If Applicable)
4. Locate Intersecting Cell Span
5. Handle Merged/Spanning Cells
6. Validate Table Evidence
7. Format Final Answer Tag
