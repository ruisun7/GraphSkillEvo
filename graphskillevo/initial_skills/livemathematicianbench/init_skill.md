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

### Compare Options
- Compare all options before committing. The correct choice is often the strongest statement justified by the question, while nearby distractors are weaker, overstrong, or miss an equality case.
- Track exact quantifiers such as "there exists", "for every", "if and only if", and "exactly when".
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
1. Compare Options
2. Select Final Answer
