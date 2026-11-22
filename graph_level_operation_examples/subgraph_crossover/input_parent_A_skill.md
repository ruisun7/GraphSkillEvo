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

### Format Final Answer Tag
- Put the final concise answer inside `<answer>...</answer>` tags.
- If the answer is not visible, use the most defensible outcome (e.g., “not visible in document”) without making up content.

## Task Graphs

### Direct Single-Span Extraction
**Use when:** The question asks for one value that appears as readable text/number/date somewhere in the document (no complex multi-step derivation needed).

**Workflow:**
1. Parse Question Intention
2. Scan Document for Candidate Spans
3. Select Best-Matching Exact Span
4. Validate Span Against Question Constraints
5. Format Final Answer Tag
