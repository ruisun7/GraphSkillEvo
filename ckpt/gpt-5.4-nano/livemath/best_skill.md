# Live Mathematical MCQ Heuristics

## Global Guidance

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

### Meta-Option Scan
- Scan the answer choices and mark any *meta-options* whose text indicates something like:
  - “One of the remaining options is correct, but a stronger result can be proven.”
  - or any variant that explicitly claims the “strongest provable statement” is not among the explicitly stated non-meta candidates.
- For each meta-option, restate (in your own words) what it implies about:
  1) whether at least one non-meta option is correct, and
  2) whether an even stronger statement (beyond the listed non-meta options) can be proved.
- Keep these notes for the maximality check; do not pick an option yet.

### Strength Hierarchy & Maximality Check
- Create a dominance assessment among the **non-meta** (explicit) options by comparing their *strength* using only the option text, focusing on:
  - **Quantifiers**: “for every ε” vs “there exists δ”, “liminf” vs “limsup”, “all x” vs “there exist x”, “if and only if” vs “if”.
  - **Exponents / powers / rates**: for bounds of the form \(n(B)\ll B^{\text{exponent}+\varepsilon}\), treat the **smaller** exponent as stronger; for lower bounds treat the **larger** growth exponent as stronger.
  - **Scope of conclusions**: conclusions that hold on a larger domain (e.g., ​\(B\to\infty\) vs subsequence \(B_j\to\infty\), \((0,T] \) vs \([0,T]\), or “without excluding exceptional cases”) are typically stronger.
  - **Extra conditions / equality clauses**: statements asserting a tighter equality characterization (e.g., “equality iff …” with a precise structure) are typically stronger than a bare inequality.
- Decide whether you can certify a **single strictly strongest** non-meta option from the option text alone.
  - If yes, label it the maximal candidate.
  - If no (e.g., competing unknown parameters like “there exists δ”, mixed liminf/limsup, or unclear dominance between different functional forms), conclude that maximality **cannot** be certified purely from the choices.
- If maximality cannot be certified and a meta-option claiming “a stronger result can be proven” is present, treat that meta-option as the best-supported choice, because the question asks for the strongest provable statement.

### Compare Options
- Compare all options (including any meta-options) before committing.
- Track exact quantifiers such as “there exists”, “for every”, “if and only if”, and “exactly when”.
- Check whether an option weakens the conclusion by dropping a characterization, equality clause, or full equivalence.
- Check whether an option overstates the theorem by upgrading regularity, removing scale restrictions, or changing an existential statement into a universal one.
- Verify the hypotheses and domain carefully. Distractors often keep the theorem shape but alter the required assumptions.
- Pay close attention to equality cases, extremal conditions, and whether a result applies to the full family or only a restricted subfamily.

### Select Final Answer
- Output the final answer as the single option label only.

---

## Task Graphs

### General Problem
**Use when:** Solve a live mathematical multiple-choice question and select the final option label.

**Workflow:**
1. Meta-Option Scan
2. Strength Hierarchy & Maximality Check
3. Compare Options
4. Select Final Answer
