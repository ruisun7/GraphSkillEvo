# DocVQA Skill: Direct Visual Text Extraction

## Global Guidance

### Overview
This skill helps the agent answer DocVQA questions by extracting the smallest exact text span (or number/date) directly from visible document evidence.

### General Principles
- Use only information that is clearly visible in the document image.
- Prefer the smallest exact span that answers the question.
- Copy text/values exactly (spelling, casing, punctuation, units) when possible.
- If multiple candidates exist, select the one with the strongest surrounding contextual match.
- Do not invent missing details; if the answer is not visible, respond with the best-supported “not found” style outcome.

### Graph-structured Skill Execution Guide
- Select the matching task graph in **Task Graphs**.
- Execute its workflow as an ordered list of node names.
- Inside each node, follow the node instructions in **Node Lists**.

## Node Lists

### Parse Question Intention
- Read the question and identify what the answer type is (name/number/date/text span/location/table cell-like value).
- Note any constraints: unit, format (e.g., “YYYY-MM-DD”), specific field name, or required exact wording.
- Determine whether the question asks for a single value or could accept multiple values.
- Determine whether the likely answer is (a) a free-standing visible span in the document or (b) a specific table cell requiring header/row selection.

### Scan Document for Candidate Spans
- Scan the document visually for label(s) or cues matching the question intent.
- Look for exact strings that appear to be the answer (including dates, IDs, quantities).
- Collect 2–5 top candidates with their immediate surrounding context (label headers, row/column headers, nearby punctuation).

### Select Best-Matching Exact Span
- Choose the candidate whose local context best matches the question.
- If there are near-matches, compare their adjacent labels/headers and layout position.
- Resolve ambiguity by selecting the one that is most directly supported by the question text.

### Validate Span Against Question Constraints
- Confirm the selected span satisfies all question constraints (exact field, unit, formatting, and whether it is the correct row/section).
- If formatting matters (e.g., date), ensure the exact visible format is copied.
- If any required constraint cannot be verified visually, treat the answer as not visible.

### Identify Relevant Table and Axes
- Locate all visible tables in the document.
- Determine which table is relevant by matching question keywords to table headers or surrounding captions.
- Identify the “row axis” (row headers/leftmost labels) and the “column axis” (top headers).
- If multiple header rows exist, note the full header path needed to reach the correct column.

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
- Confirm the extracted value is directly inside the correct cell region.
- If the correct row/column intersection cannot be verified visually (e.g., ambiguity from merges/cropping), treat the answer as not visible.

### Format Final Answer Tag
- Put the final concise answer inside `<answer>...</answer>` tags.
- If the answer is not visible, use `not visible in document` inside the tags.

## Task Graphs

### Direct Single-Span Extraction
**Use when:** The question asks for one value that is readable as a single text/number/date span somewhere in the document, without requiring table row/column header intersection.

**Workflow:**
1. Parse Question Intention
2. Scan Document for Candidate Spans
3. Select Best-Matching Exact Span
4. Validate Span Against Question Constraints
5. Format Final Answer Tag

### Table Cell Retrieval
**Use when:** The question asks for a value from a table or clearly requires selecting a specific cell using nearby headers/row labels.

**Workflow:**
1. Parse Question Intention
2. Identify Relevant Table and Axes
3. Extract Row Key (If Applicable)
4. Extract Column Key (If Applicable)
5. Locate Intersecting Cell Span
6. Handle Merged/Spanning Cells
7. Validate Table Evidence
8. Format Final Answer Tag
