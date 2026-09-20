# Question Answering Skill

## Global Guidance

### General Principles

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

### Ingest Question and Determine Target Answer Form
Read the question and decide:
- **Answer type**: person name, quoted title/phrase, a company/trademark, a common noun (category/head noun), or a dictionary/slang word.
- **Expected granularity** (for exact match):
  - If the question asks for a *short regnal/common name* (e.g., “this king of …”), prefer the commonly used form (e.g., “King X”) over longer full names.
  - If the question is about an *event* with qualifiers (e.g., “Olympic distance triathlon”), determine whether only the **head noun** (e.g., “Triathlon”) is expected.
  - If the question is about a *gift/company slogan* and the evidence shows a longer legal name (e.g., “Hallmark Cards”), determine whether only the brand name is expected (e.g., “Hallmark”).
  - If the question contains an *ampersand co-name* pattern (e.g., “Publishing partners: ___ & Wagnalls”), decide whether the expected output is the **full co-name including “& …”**.
  - If the question looks like a *crossword/dictionary clue* (e.g., ends with “(4)” and uses descriptor words), decide whether the expected output is the **single slang/dictionary-defined word** matching the descriptor.
- **What constraints must be present in the evidence**: extract must-match items such as
  - school names (e.g., Harrow, Sandhurst),
  - exact quoted slogan fragments,
  - specific numbers/distances,
  - fixed partner names in an ampersand phrase,
  - or descriptor keywords.
Keep this decision as internal guidance for later extraction and post-processing.

### Find Evidence Spans in Context
Using keywords from the question, scan the provided context passages and select the sentence(s) most directly supporting the needed fact.
- Prefer lines that explicitly mention the relevant person/entity/phrase **and** contain at least one key constraint from the question (names, numbers, slogan fragments, etc.).
- If multiple candidate sentences exist, allow them to remain candidates; do not commit yet if they may differ on required constraints.
- If the question references a pronoun tied to a person/entity, ensure you also capture the sentence that provides the antecedent.
- If the question describes a transformation, capture both the transformation description and the referenced phrase.

### Verify Evidence Meets Key Constraints
From the candidate evidence spans found, select the span(s) that satisfy **all** must-match constraints derived in **Ingest Question and Determine Target Answer Form**.
- If a constraint is a specific number/distance, require that number (or an unambiguous close numeric form) appears in the selected span.
- If constraints include multiple education institutions, require the selected span contains **all** named institutions in that single person/subject description.
- If constraints include a quoted slogan, require the selected span contains the slogan wording (or an obvious contiguous portion).
- If constraints include a fixed partner (e.g., “Wagnalls”), require that the selected span contains that fixed partner name.
- If more than one span still matches, pick the one where the expected answer entity is closest to the constraints (e.g., the same sentence tying the person to the education/slogan).

### Extract Answer Candidate from Evidence
From the selected evidence:
- Extract the minimal text span that directly answers the question as determined by **Ingest Question and Determine Target Answer Form**.
- For pronouns, replace the pronoun with the correct antecedent mentioned in the evidence.
- For entity questions, extract just the entity name/title (not an entire declarative sentence).
- For dictionary/slang-style clues, extract the **defined word** (the single term the evidence identifies as the meaning).

### Extract Regnal/Common Name from Full Person Name
When the evidence contains a full formal name (e.g., with patronymics) but the question expects a common regnal/common form:
- Reduce to the commonly used regnal/common name present in the evidence (e.g., keep “King Hussein” rather than a longer “King Hussein bin Talal”).
- Remove extra components like “bin …” / patronymic parts if the question does not ask for them.

### Handle Transformation/Contrast Wording
If the question indicates a transformation (e.g., “changed ‘X’ to ‘Y’”):
- Determine which variant the question expects as the final answer (typically the original/standard wording tied to the referenced title, unless the question explicitly requests the changed form).
- Extract the expected variant consistently with the question’s wording.

### Strip Qualifiers to Return Head Noun
If the question expects a base category/head noun from a longer phrase:
- Remove leading qualifiers/adjectives (e.g., “Olympic distance …” -> keep only the core category noun like “Triathlon”).
- Keep conjunction structure only if it is part of the head noun/category; otherwise return a single-word/single-category output.

### Trim Company Brand Name
If the question expects a short company/brand/trademark name but the evidence provides a longer legal name:
- Remove common corporate suffixes/containers: “Cards”, “Inc.”, “Company”, “Co.”, “Limited”, “LLC”, “Corporation”, etc.
- Keep the distinctive brand portion (e.g., transform “Hallmark Cards” -> “Hallmark”).

### Handle Ampersand Partner Phrases
If the question involves an ampersand co-name and the expected output is the full partnered name:
- If evidence contains a co-name like “X & Y” or “X and Y”, return it in the most exact phrasing form consistent with the evidence and the question (including the “&” if it appears in the expected style).
- Do **not** truncate to only the first partner if the question blank can cover the paired phrase (e.g., return “Funk & Wagnalls” rather than just “Funk”).

### Constrain to Minimal Answer Form
Adjust the extracted candidate to match the expected granularity:
- If the question asks for a base category noun (e.g., head noun/category), return only that noun (not a longer descriptive string).
- If the question expects an entity only, remove wrappers/extra phrases (e.g., avoid including surrounding context like “Hallmark Cards is …”).
- If the evidence extraction accidentally includes extra modifiers (including leading descriptor words), trim them away.
- Avoid returning boolean scaffolding or explanatory text; keep only the answer string.

### Normalize for Exact-Match
Apply string normalization aimed at exact-match:
- Remove leading/trailing quotation marks and normalize whitespace.
- Convert curly apostrophes/quotes to straight ASCII equivalents.
- Remove diacritics from letters.
- Replace common punctuation variants consistently (e.g., use “&” where appropriate if the evidence/question uses it).
- Strip boolean scaffolding prefixes (e.g., remove any leading “True — ” or similar) if present.

### Format Final Answer
Output the final answer as:
<answer>...</answer>
Inside the tags, include only the normalized minimal answer string.

## Task Graphs

### Title/phrase transformation questions (changed X to Y)
**Use when:** The question includes transformation/contrast wording like “changed”, “substituted”, “from … to …”, or references an “original” vs “modified” title/phrase.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Handle Transformation/Contrast Wording
6. Constrain to Minimal Answer Form
7. Normalize for Exact-Match
8. Format Final Answer

### Person identification from biographical clues or pronoun antecedents
**Use when:** The question asks “who”/“his/her/he” in a way that requires identifying a person tied to works/events, and the expected answer is a person name without requiring regnal/common-name trimming.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Constrain to Minimal Answer Form
6. Normalize for Exact-Match
7. Format Final Answer

### Education-at specific institutions with short regnal/common-name expectation
**Use when:** The question asks for “this current king of …” (or similar role-based phrasing) and mentions education at specific institutions (e.g., in England at multiple schools) where the evidence may include multiple kings.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Extract Regnal/Common Name from Full Person Name
6. Constrain to Minimal Answer Form
7. Normalize for Exact-Match
8. Format Final Answer

### Event name with numeric distance qualifier (head noun expected)
**Use when:** The question asks for the name of an event that covers a specific numeric distance/time, and the context/evidence may contain a longer qualified event name where the expected answer is the underlying head noun.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Strip Qualifiers to Return Head Noun
6. Constrain to Minimal Answer Form
7. Normalize for Exact-Match
8. Format Final Answer

### Gift company slogan: brand/trademark name expected (not legal company name)
**Use when:** The question references a “gift company” and includes a slogan in quotes, expecting the short brand/company name.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Trim Company Brand Name
6. Constrain to Minimal Answer Form
7. Normalize for Exact-Match
8. Format Final Answer

### Ampersand co-name / publishing partners (full paired name expected)
**Use when:** The question contains an ampersand co-name structure (e.g., “___ & Wagnalls” or similar), where the blank can correspond to a full partnered entity name.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Handle Ampersand Partner Phrases
6. Constrain to Minimal Answer Form
7. Normalize for Exact-Match
8. Format Final Answer

### Crossword/dictionary clue (descriptor + (N))
**Use when:** The question looks like a crossword/dictionary clue using descriptor words and ends with a parenthesized length like “(4)”.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Constrain to Minimal Answer Form
6. Normalize for Exact-Match
7. Format Final Answer

### Questions expecting a base category noun (not a longer name)
**Use when:** The question asks for a generic category/base noun and not a full longer descriptive phrase.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Constrain to Minimal Answer Form
6. Normalize for Exact-Match
7. Format Final Answer

### Multi-item list prompts where only one item is expected
**Use when:** The question prompt appears to be a short comma-separated list or otherwise formatted such that only one item is expected as the final answer.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Constrain to Minimal Answer Form
6. Normalize for Exact-Match
7. Format Final Answer

### Generic direct extraction (default)
**Use when:** None of the specialized patterns above apply.

**Workflow:**
1. Ingest Question and Determine Target Answer Form
2. Find Evidence Spans in Context
3. Verify Evidence Meets Key Constraints
4. Extract Answer Candidate from Evidence
5. Constrain to Minimal Answer Form
6. Normalize for Exact-Match
7. Format Final Answer
