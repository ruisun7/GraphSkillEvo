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
- Read the question and identify: the requested attribute (what to answer) and any constraints (e.g., person, date, section, unit, “according to”, “where”).
- Determine expected answer type: short text, number, date, or phrase.

### Locate Candidate Evidence
- Scan the document image for text regions likely related to the question (matching keywords from the question).
- Consider headings, labels, and nearby context (e.g., “Total”, “Date”, “Author”, “Amount”).
- If the page is dense, prioritize regions with strong semantic matches to question keywords.

### Extract Smallest Exact Span
- From the best candidate region, extract the smallest contiguous span that directly provides the answer.
- Preserve exact formatting as shown (spelling, punctuation, capitalization, digit grouping, units).
- If the value is part of a longer line, select only the value portion.

### Resolve Near-Matches
- If multiple candidate spans appear similar, compare their surrounding labels/layout.
- Choose the candidate where the nearest label/context most precisely matches the question constraints.
- If still unclear, re-check the full region for a closer match.

### Validate Answer Support
- Verify the extracted span is explicitly present and readable in the document.
- Ensure it matches the question’s requested attribute and constraints (e.g., correct date, correct field name).
- If no explicit support is found, do not guess.

### Format Final Answer
- Output exactly: `<answer>...extracted text...</answer>`.
- If not found: `<answer>Not found in the document</answer>`.

## Task Graphs
### Single-Span Direct Question
**Use when:** The question asks for one direct value/span and can be answered from a single visible location.

**Workflow:**
1. Parse Goal
2. Locate Candidate Evidence
3. Extract Smallest Exact Span
4. Resolve Near-Matches
5. Validate Answer Support
6. Format Final Answer
