# DocVQA Skill: Span Extraction (Single-Answer)

## Global Guidance
### Overview
Solve DocVQA questions by extracting the smallest exact visible text span that answers the question, then formatting the response in `<answer>...</answer>` tags.

### General Principles
- Use only visible evidence from the provided document image.
- Prefer the smallest exact span that directly answers the question.
- Copy text exactly (names, numbers, dates, units) when the question asks for a specific value.
- If multiple similar spans exist, choose the one whose nearby labels/layout best match the question.
- Do not invent missing information; if evidence is insufficient, return a best-supported statement like `Not found in the document`.

### Graph-structured Skill Execution Guide
Follow the matching **Task Graph**. For the selected workflow, execute nodes in order.
1. Execute each node exactly in the listed order.
2. Apply the node instructions from **Node Lists**.
3. The final output must be the concise answer wrapped in `<answer>...</answer>` tags.

## Node Lists
### Parse Goal
- Read the question and identify:
  - the requested attribute(s) (what to answer)
  - any constraints/anchors (e.g., “Exhibit No”, “company”, “according to”, “where”, related phrases)
- Determine expected answer type: short text, number, date, or phrase.
- Extract up to 3 anchor keywords/labels from the question that should appear near the answer in the document (e.g., the literal label “Exhibit No” when asked).

### Locate Candidate Evidence
- Scan the document image for text regions likely related to the question using:
  - the anchor keywords/labels
  - likely UI patterns like a field label followed by a value
- Prioritize evidence where the field label/value relationship is visually clear:
  - for label-based questions (e.g., “Exhibit No”), prefer regions where the label and the candidate value are near each other.
  - for company/name questions, prefer regions where the company name is explicitly tied to the requested context phrase.
- If the page is dense, prefer regions with the strongest semantic match *and* strongest label/value proximity.

### Extract Smallest Exact Span
- From the best candidate region, extract the smallest contiguous span that directly provides the answer.
- Preserve exact formatting as shown in the document (spelling, punctuation, capitalization, digit grouping, units, and internal spaces).
- If the value is part of a longer line, select only the value portion.

### Resolve Near-Matches
- If multiple candidate spans appear similar (especially similar-looking numbers/IDs):
  - choose the candidate whose *nearest surrounding label/context* best matches the question’s requested attribute/anchor keywords
  - for label-based questions, prefer the value immediately associated with the requested label (e.g., “Exhibit No”).
- If still unclear, re-check the full region for a closer match rather than picking a different number.

### Validate Answer Support
- Verify the extracted span is explicitly present and readable in the document.
- Ensure it matches the question’s requested attribute and constraints.
- Additional checks:
  - If the question asks for a labeled field (e.g., “Exhibit No”), confirm the extracted value is visibly linked to that label (adjacent or clearly paired).
  - If the question is asking for multiple related values (e.g., “height and width”), confirm each value is present and associated with the correct attributes.
- If no explicit support is found, do not guess.

### Unescape Formatting for Output
- Before final formatting, convert common OCR/encoding artifacts to the literal characters expected in the answer:
  - `&quot;` or `&#34;` → `"`
  - `&amp;` → `&`
- Trim only leading/trailing whitespace; do not alter internal spacing that appears in the document.

### Format Final Answer
- Output exactly: `<answer>...extracted text...</answer>`.
- If not found: `<answer>Not found in the document</answer>`.

## Task Graphs
### Single-Span Direct Question
**Use when:** The question asks for one direct value/span (including cases where the answer contains multiple values that are still explicitly co-located) and can be answered from visible text.

**Workflow:**
1. Parse Goal
2. Locate Candidate Evidence
3. Extract Smallest Exact Span
4. Resolve Near-Matches
5. Validate Answer Support
6. Unescape Formatting for Output
7. Format Final Answer
