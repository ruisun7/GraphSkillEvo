## Global Guidance

### Overview
This skill handles spreadsheet tables (and worksheet-level edits) that need cleansing, filtering, sorting, aggregation, reshaping, or derived-column / conditional-retrieval logic.

### General Principles
- Use **pandas** for bulk table transformations and **openpyxl** for loading/saving and for cell-accurate writeback.
- Never use any other third-party libraries.
- Discover table/used bounds from the workbook itself; do not hardcode row counts, column letters, or rely on truncated previews.
- Preserve sheets and cells not mentioned in the instruction.
- **Do not rely on Excel to evaluate formulas.** Even if the user asks to “create a formula”, compute the intended result in Python and write the resulting literal value(s).
- **Coordinate fidelity:** when an instruction specifies an exact sheet/range (or target cell like K6), the writeback must address that exact location; do not “approximate” by targeting the wrong row/column offsets.
- Ensure target outputs are never left as `None`/blank when a concrete value is expected; always write a value (or an explicit empty marker like `"-"` when requested).
- Normalize text for lookups/mappings (trim whitespace, compare case-insensitively for keys like labels/codes).
- For arithmetic inputs, treat common “missing” numeric markers (`None`, `""`, `"-"`, `"–"`, `"—"`) as **0 for computation**. Then apply any *presentation* rule (e.g., display `"-"` instead of 0) only to the specified output column(s) when the instruction calls for it.
- When the task says to **ignore empty/blanks**, ensure blanks contribute nothing to aggregations/conditions and that the corresponding output cells follow the instruction’s required behavior (blank marker vs numeric 0 vs computed value).
- Date/interval logic: when conditional retrieval is based on date ranges (including “adjacent” or “previous/next” bounds), convert to a consistent date basis (date-only, ignoring time) and implement the interval inclusively/exclusively exactly as implied (typically inclusive endpoints). Guard against missing/invalid adjacent bounds.
- Avoid rewriting the entire workbook; update only the affected cells/ranges.

### Graph-structured Skill Execution Guide
- Pick exactly one task graph that matches the instruction’s intent.
- Execute the required node names **in the given order**; do not skip validation or writeback steps.
- Use Extract/Transform/Prepare/Writeback/Validate so that the *exact requested cell/range(s)* receive the **computed, non-formula literal** result when required.
- During validation, confirm:
  1) the target coordinates/range were addressed exactly (no off-by-one, no missing rows/columns),
  2) every cell in the requested output range has a value when the specification expects a concrete value,
  3) computed logic matches the intended transformation (including correct handling of blanks and conditional/adjacent-date windows), and
  4) unaffected workbook content remains unchanged.
- If any part fails (e.g., target range mismatch, missing headers, unexpected input shapes, or any target cell remains `None`), recover by re-inspecting workbook bounds/headers and re-applying the computation before saving.

### Node List boundary
Only the guidance above applies globally; workflow-specific mechanics remain governed by the node instructions.

## Node Lists

### Parse Request
- Identify: (a) which sheet(s) contain the source tables, (b) which sheet/range is the target output, (c) the transformation intent (filter/sort, aggregation/derived column, standardization, or multi-sheet match-and-sum), and (d) key columns used to match rows (e.g., “TY” and “OR” style keys).
- Identify which output columns require computed values (e.g., a derived “BALANCE” = SALE - RET), and which columns should *preserve* original values.
- Identify presentation rules by column (examples to look for):
  - where blanks should display as `"-"` instead of `0`
  - where negative values should get red text (hex `#FF0000`)
  - where headers should be un-bolded and left-aligned
  - where numeric vs text alignment should be applied (e.g., right-align vs left-align)
- Note whether any required output must be numeric (float) rather than integers, and whether Excel formulas must be replaced by literal computed values.
- Extract the expected target range/range size from the instruction (do not assume a fixed row count).

### Inspect Workbook
- Load the workbook with openpyxl.
- Enumerate sheet names.
- For each relevant sheet:
  - Determine a reliable used area by scanning for the last non-empty cell in rows/columns that contain the expected headers (do not rely solely on ws.max_row if trailing empty rows exist).
  - Locate the header row by searching for the requested header labels (case-insensitive, whitespace-trimmed). If a header row is already known by the instruction, still verify it exists.
- Record:
  - sheet names involved
  - header row index/indices
  - column indices for every referenced header label
  - the candidate data row start (first row after headers) and last row (last row with any non-empty value in the referenced columns)

### Discover Multi-Sheet Keys
- Specifically for tasks that build/extend a “collection”-type table from multiple similarly-structured source sheets:
  - For the target collection sheet, read the existing ordered list of match keys (e.g., pairs like (TY, OR) from the relevant columns) in the current row order.
  - For each source sheet:
    - Read its rows in sheet order and build rows keyed by the normalized key tuple.
    - Aggregate numeric fields to be summed (e.g., SALE columns summed; RET columns summed) for each key tuple.
  - Decide which keys are already present in the collection sheet (update them) vs missing (append them) while ensuring:
    - existing collection row order is preserved
    - missing keys are appended at the bottom in the order of first appearance across the source sheets
- Keep track of “missingness flags” per contributing component (e.g., whether SALE was blank/marker on a given row, whether RET was blank/marker on a given row). This is needed to apply `"-"` presentation rules correctly.

### Extract Table
- Extract each referenced table region into an internal structure for computation.
- Prefer pandas when available, but **never assume pandas is installed**:
  - Attempt to import pandas inside this node.
  - If pandas import fails, extract using pure Python lists/dicts from openpyxl cells.
- Preserve column meanings:
  - Use the located header row to define columns.
  - Keep original column order.
- For numeric columns:
  - Parse numeric-like strings into numbers.
  - Treat `None`, `""`, `"-"`, `"–"`, `"—"` as **0 for computation**, but also store a per-cell missing marker flag so presentation rules can be applied later.
- Normalize key columns for matching:
  - Trim whitespace, compare case-insensitively.
- Do not drop rows that appear structurally valid; only drop rows that are fully empty across the referenced columns.

### Transform Data
- Apply the requested transformation using the extracted data.
- For aggregation/derived logic:
  - If a derived column is requested (e.g., BALANCE = SALE - RET), compute it in Python as a numeric value.
  - Replace any formula-like placeholders in the target (e.g., cells containing `"=E2-F2"`) with the computed literal result.
- Apply presentation rules with column specificity:
  - If the instruction says blanks should display as `"-"` instead of zero, apply this only to the specified output column(s) (e.g., the derived column) and only when the computed value is the result of missing inputs according to the stored missingness flags.
  - Do not replace zeros in source/other columns unless explicitly requested.
- Aggregation across sheets (multi-sheet match-and-sum):
  - Sum across all sheets where the key tuple matches.
  - Do not reorder existing collection rows.
  - After appending/mutating collection rows, recompute any “index/item number” column (e.g., ITEM) as a sequential value matching the final row order.
    - When the instruction expects float-like values (e.g., `1.0`), write floats (not ints) for this index column.
- Type correctness:
  - Write computed numeric outputs as floats when the source values are floats or when float outputs are expected by the instruction.

### Prepare Writeback
- Decide writeback strategy:
  - Overwrite only the target table/range cells that correspond to the computed/updated columns.
  - If expanding a collection table, compute exact insertion/append row endpoints and ensure cells beyond the written range remain unchanged.
- Build a mapping from transformed rows/columns to workbook coordinates using the header column indices and discovered header/data start rows.
- If the target range currently contains old computed values (formulas or stale literals), clear only the affected cells/range before writing.
- Ensure the write plan includes every cell in the requested output range and none are left unspecified.

### Write Back Safely
- Write only the affected cells/ranges.
- Formula handling:
  - If the instruction expects computed values, write literal values (numbers/strings) rather than formulas.
- Merged-cell safety:
  - Before writing, detect whether a target cell is part of a merged range.
  - If merged, write to the top-left cell of that merged range only (or skip if doing so would overwrite unrelated expected content).
- Formatting constraints:
  - Update formatting only where requested:
    - unbold headers and left-align headers
    - set font to Calibri 11pt and unbold all text within the affected target range (and/or specified columns)
    - apply red font color `#FF0000` to negative values in the specified derived output column(s)
    - apply alignment per column instructions (e.g., right-align numeric columns A/E/F/G; left-align B/C/D)
  - Preserve all other formatting not explicitly requested.
- Ensure no computed target cell is left as `None`:
  - If a value is required, write the computed value or `"-"` per the output column’s presentation rule.

### Validate Result
- Confirm all of the following:
  1. The expected target sheet/range coordinates were addressed (no off-by-one, no missing rows/columns).
  2. Every cell in the requested output range has a value when a concrete value is expected (not `None`).
  3. Computed outputs match the intended logic:
     - derived column = SALE - RET
     - aggregation across multi-sheet keys uses summed contributions
     - missing-input presentation rules are applied only to the correct output columns
     - appended keys preserve existing row order and new keys are appended correctly
  4. Formatting checks relevant to the instruction:
     - header boldness/alignment
     - unbold + Calibri 11 within the intended scope
     - negative derived values red
     - alignment per specified columns
  5. Unaffected workbook content remains unchanged (e.g., other sheets/tables not in the target range).
- If validation fails:
  - re-run Inspect Workbook to re-derive bounds/headers
  - re-extract and re-apply transformation
  - redo writeback for the corrected target range before saving.

### Save Output
- Save the workbook to OUTPUT_PATH.

## Task Graphs

### Filter, Sort, or Reorder Table
**Use when:** The task requires selecting rows, sorting records, or reordering columns in a tabular sheet.
**Workflow:**
1. Parse Request
2. Inspect Workbook
3. Extract Table
4. Transform Data
5. Prepare Writeback
6. Write Back Safely
7. Validate Result
8. Save Output

### Aggregate, Summarize, or Create a Derived Table
**Use when:** The task asks for totals, counts, grouped summaries, pivots, or a new derived-column/derived-range result within a single sheet (including replacing formula results with literal computed values).
**Workflow:**
1. Parse Request
2. Inspect Workbook
3. Extract Table
4. Transform Data
5. Prepare Writeback
6. Write Back Safely
7. Validate Result
8. Save Output

### Clean or Standardize Table Values
**Use when:** The task asks to normalize text, fix blanks, convert types, recode categories, or repair inconsistent entries across many rows.
**Workflow:**
1. Parse Request
2. Inspect Workbook
3. Extract Table
4. Transform Data
5. Prepare Writeback
6. Write Back Safely
7. Validate Result
8. Save Output

### Multi-Sheet Match-and-Sum Collection Table
**Use when:** The task requires matching and aggregating rows across multiple sheets into a single “collection”/summary table using key columns (e.g., TY and OR), then computing one or more derived columns (e.g., BALANCE) and writing literal computed outputs (not formulas) while preserving existing row order and appending only missing keys.
**Workflow:**
1. Parse Request
2. Inspect Workbook
3. Discover Multi-Sheet Keys
4. Extract Table
5. Transform Data
6. Prepare Writeback
7. Write Back Safely
8. Validate Result
9. Save Output
