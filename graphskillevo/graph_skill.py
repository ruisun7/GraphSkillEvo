"""Helpers for graph-structured skill documents."""
from __future__ import annotations

import re
from dataclasses import dataclass


_GLOBAL_GUIDANCE_RE = re.compile(r"(?im)^##\s+Global Guidance\s*$")
_NODE_LISTS_RE = re.compile(r"(?im)^##\s+Node Lists\s*$")
_TASK_GRAPHS_RE = re.compile(r"(?im)^##\s+Task Graphs\s*$")
_H1_RE = re.compile(r"^#(?!#)[ \t]+(.+?)\s*$")
_H2_RE = re.compile(r"(?m)^##(?!#)[ \t]+(.+?)\s*$")
_H3_RE = re.compile(r"(?m)^###(?!#)[ \t]+(.+?)\s*$")
_USE_WHEN_RE = re.compile(r"(?m)^\*\*Use when:\*\*[ \t]*(.*?)\s*$")
_WORKFLOW_RE = re.compile(r"(?m)^\*\*Workflow:\*\*[ \t]*$")
_WORKFLOW_ITEM_RE = re.compile(r"^([0-9]+)\.[ \t]+(.+?)\s*$")
_REQUIRED_SECTION_NAMES = ("Global Guidance", "Node Lists", "Task Graphs")


@dataclass(slots=True)
class GraphSkillParts:
    global_guidance: str
    node_lists: str
    task_graphs: str


@dataclass(slots=True)
class _StrictGraphSkillParts:
    global_guidance_body: str
    node_lists_body: str
    task_graphs_body: str


def split_graph_skill(content: str) -> GraphSkillParts:
    """Split a graph skill into Global Guidance, Node Lists, and Task Graphs."""
    text = str(content or "")
    global_match = _GLOBAL_GUIDANCE_RE.search(text)
    node_match = _NODE_LISTS_RE.search(text)
    task_match = _TASK_GRAPHS_RE.search(text)
    if global_match is None:
        raise ValueError("graph skill must contain a '## Global Guidance' heading")
    if node_match is None:
        raise ValueError("graph skill must contain a '## Node Lists' heading")
    if task_match is None:
        raise ValueError("graph skill must contain a '## Task Graphs' heading")
    if global_match.start() >= node_match.start():
        raise ValueError("'## Global Guidance' must appear before '## Node Lists'")
    if node_match.start() >= task_match.start():
        raise ValueError("'## Node Lists' must appear before '## Task Graphs'")
    return GraphSkillParts(
        global_guidance=text[: node_match.start()].rstrip(),
        node_lists=text[node_match.start() : task_match.start()].rstrip(),
        task_graphs=text[task_match.start() :].rstrip(),
    )


def compose_graph_skill(parts: GraphSkillParts) -> str:
    """Compose graph skill sections into a complete markdown document."""
    return (
        parts.global_guidance.rstrip()
        + "\n\n"
        + parts.node_lists.rstrip()
        + "\n\n"
        + parts.task_graphs.rstrip()
        + "\n"
    )


def assert_graph_skill(content: str) -> None:
    """Validate that content follows the expected graph skill structure."""
    parts = _split_graph_skill_strict(content)
    _assert_global_guidance(parts.global_guidance_body)
    node_names = _parse_node_lists(parts.node_lists_body)
    referenced_names = _parse_task_graphs(parts.task_graphs_body)

    undefined = referenced_names - node_names
    if undefined:
        raise ValueError(f"task graph references undefined nodes: {sorted(undefined)}")
    unused = node_names - referenced_names
    if unused:
        raise ValueError(f"node list contains unused nodes: {sorted(unused)}")


def _split_graph_skill_strict(content: str) -> _StrictGraphSkillParts:
    text = str(content or "")
    h2_matches = list(_H2_RE.finditer(text))
    by_name: dict[str, list[re.Match[str]]] = {name: [] for name in _REQUIRED_SECTION_NAMES}
    unexpected: list[str] = []

    for match in h2_matches:
        name = match.group(1).strip()
        if name in by_name:
            by_name[name].append(match)
        else:
            unexpected.append(name)

    for name in _REQUIRED_SECTION_NAMES:
        matches = by_name[name]
        if not matches:
            raise ValueError(f"graph skill must contain a '## {name}' heading")
        if len(matches) > 1:
            raise ValueError(f"graph skill must contain exactly one '## {name}' heading")
    if unexpected:
        raise ValueError(f"graph skill contains unexpected '##' sections: {sorted(unexpected)}")

    global_match = by_name["Global Guidance"][0]
    node_match = by_name["Node Lists"][0]
    task_match = by_name["Task Graphs"][0]
    if not (global_match.start() < node_match.start() < task_match.start()):
        raise ValueError("'## Global Guidance', '## Node Lists', and '## Task Graphs' must appear in that order")

    _assert_allowed_preamble(text[: global_match.start()])

    return _StrictGraphSkillParts(
        global_guidance_body=text[global_match.end() : node_match.start()],
        node_lists_body=text[node_match.end() : task_match.start()],
        task_graphs_body=text[task_match.end() :],
    )


def _assert_allowed_preamble(preamble: str) -> None:
    lines = [line.strip() for line in preamble.splitlines() if line.strip()]
    if not lines:
        return
    if len(lines) == 1 and _H1_RE.fullmatch(lines[0]):
        return
    raise ValueError("only an optional '# <Skill Name>' title may appear before '## Global Guidance'")


def _assert_global_guidance(body: str) -> None:
    # Any ### subsection name is allowed here; strict ## checks are handled globally.
    del body


def _parse_node_lists(body: str) -> set[str]:
    blocks = _parse_h3_blocks(body, section_name="Node Lists", block_kind="node")
    if not blocks:
        if _has_non_separator_text(body):
            raise ValueError("'## Node Lists' must be empty or contain '### <Node Name>' headings")
        return set()

    names: list[str] = []
    seen: set[str] = set()
    for name, _body in blocks:
        if not name:
            raise ValueError("node heading in '## Node Lists' must be non-empty")
        if name in seen:
            raise ValueError(f"duplicate node heading in '## Node Lists': {name!r}")
        seen.add(name)
        names.append(name)
    return set(names)


def _parse_task_graphs(body: str) -> set[str]:
    blocks = _parse_h3_blocks(body, section_name="Task Graphs", block_kind="task graph")
    referenced_names: set[str] = set()
    if not blocks:
        if _has_non_separator_text(body):
            raise ValueError("'## Task Graphs' must be empty or contain '### <Task Type>' headings")
        return referenced_names

    for task_type, task_body in blocks:
        if not task_type:
            raise ValueError("task graph heading in '## Task Graphs' must be non-empty")
        referenced_names.update(_parse_task_graph_workflow(task_type, task_body))
    return referenced_names


def _parse_h3_blocks(body: str, *, section_name: str, block_kind: str) -> list[tuple[str, str]]:
    matches = list(_H3_RE.finditer(body))
    if not matches:
        return []
    preface = body[: matches[0].start()]
    if _has_non_separator_text(preface):
        raise ValueError(f"'## {section_name}' must start with '### <{block_kind.title()} Name>' headings")

    blocks: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        name = match.group(1).strip()
        block_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        blocks.append((name, body[match.end() : block_end]))
    return blocks


def _parse_task_graph_workflow(task_type: str, body: str) -> set[str]:
    use_when_matches = list(_USE_WHEN_RE.finditer(body))
    if len(use_when_matches) != 1:
        raise ValueError(f"task graph {task_type!r} must contain exactly one '**Use when:**' line")
    use_when = use_when_matches[0]
    if not use_when.group(1).strip():
        raise ValueError(f"task graph {task_type!r} must have a non-empty '**Use when:**' description")

    workflow_matches = list(_WORKFLOW_RE.finditer(body))
    if len(workflow_matches) != 1:
        raise ValueError(f"task graph {task_type!r} must contain exactly one '**Workflow:**' line")
    workflow = workflow_matches[0]
    if use_when.start() >= workflow.start():
        raise ValueError(f"task graph {task_type!r} must place '**Use when:**' before '**Workflow:**'")
    if _has_non_separator_text(body[: use_when.start()]):
        raise ValueError(f"task graph {task_type!r} contains unexpected text before '**Use when:**'")
    if _has_non_separator_text(body[use_when.end() : workflow.start()]):
        raise ValueError(f"task graph {task_type!r} contains unexpected text between '**Use when:**' and '**Workflow:**'")

    return _parse_workflow_items(task_type, body[workflow.end() :])


def _parse_workflow_items(task_type: str, workflow_body: str) -> set[str]:
    expected_number = 1
    referenced_names: set[str] = set()
    saw_item = False
    saw_trailing_separator = False

    for line in workflow_body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "---":
            saw_trailing_separator = True
            continue
        if saw_trailing_separator:
            raise ValueError(f"task graph {task_type!r} contains unexpected text after workflow list")

        item_match = _WORKFLOW_ITEM_RE.fullmatch(line.strip())
        if item_match is None:
            raise ValueError(f"task graph {task_type!r} workflow must contain only numbered list items")

        number_text = item_match.group(1)
        if number_text != str(expected_number):
            raise ValueError(
                f"task graph {task_type!r} workflow numbering must start at 1 and be consecutive; "
                f"expected {expected_number}, got {number_text}"
            )

        node_name = item_match.group(2).strip()
        if not node_name:
            raise ValueError(f"task graph {task_type!r} workflow item {number_text} must name a node")
        referenced_names.add(node_name)
        saw_item = True
        expected_number += 1

    if not saw_item:
        raise ValueError(f"task graph {task_type!r} workflow must contain at least one numbered node")
    return referenced_names


def _has_non_separator_text(text: str) -> bool:
    return any(line.strip() and line.strip() != "---" for line in text.splitlines())


def adopt_other(parent_a: str, candidate: str) -> str:
    """Use candidate Global Guidance while preserving Parent A's graph sections."""
    parent_parts = split_graph_skill(parent_a)
    candidate_parts = split_graph_skill(candidate)
    return compose_graph_skill(
        GraphSkillParts(
            global_guidance=candidate_parts.global_guidance,
            node_lists=parent_parts.node_lists,
            task_graphs=parent_parts.task_graphs,
        )
    )


def adopt_graph(parent_a: str, candidate: str) -> str:
    """Use candidate graph sections while preserving Parent A's Global Guidance."""
    parent_parts = split_graph_skill(parent_a)
    candidate_parts = split_graph_skill(candidate)
    return compose_graph_skill(
        GraphSkillParts(
            global_guidance=parent_parts.global_guidance,
            node_lists=candidate_parts.node_lists,
            task_graphs=candidate_parts.task_graphs,
        )
    )
