# DocVQA Skill

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

### Gather Evidence
- Identify direct evidence from the document that supports the response.
- Highlight sections, phrases, or data points that are pertinent and strong.

### Confirm Evidence Credibility
- Validate that the identified evidence is from a reliable section of the document.
- Look for published or official information that solidifies the answer's validity.

### Visual Evidence Discipline
- Read the document carefully before answering.
- Prefer the smallest exact text span that answers the question.
- When several nearby strings look similar, choose the one whose surrounding labels or layout best match the question.

### Exact Answer Discipline
- Copy names, numbers, and dates exactly from the document whenever possible.
- Prefer direct extraction over paraphrase.
- Before finalizing, compare the answer against nearby alternatives and keep the best-supported exact span.

### Cite Evidence in Response
- Structurally integrate the gathered evidence into your answer where applicable.
- Note the section or page number of the evidence to reference in the final response.

## Task Graphs

### General Question
**Use when:** Answer a general DocVQA question using visual document evidence.

**Workflow:**
1. Visual Evidence Discipline
2. Exact Answer Discipline

### Evidence Support Task
**Use when:** Questions require substantiation with document evidence for assurance in answers.

**Workflow:**
1. Gather Evidence
2. Confirm Evidence Credibility
3. Cite Evidence in Response
