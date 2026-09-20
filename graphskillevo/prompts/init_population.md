You create initial graph-structured skill documents for an agent benchmark.

Generate complete, diverse skill documents that can be used directly by the target agent.
Keep each skill self-contained and practical. Use the benchmark context to infer the main task types, design suitable workflows for them, and convert recurring execution steps into reusable graph nodes.

Every skill must preserve this graph-structured organization:
1. A `## Global Guidance` section containing instructions that apply across all nodes and workflows.
2. A `## Node Lists` section containing reusable subtask nodes. Node headings should be markdown headings such as `### Parse Goal`.
3. A `## Task Graphs` section containing task-type workflows that connect node names into executable task-solving procedures.

Use this markdown layout for each skill document:

`# <Skill Name>`

`## Global Guidance`

`## Node Lists`

`## Task Graphs`

The optional title may appear before `## Global Guidance`, but the three required sections must appear exactly in this order.

Section requirements:

### `## Global Guidance`
This section contains instructions that apply across all nodes and workflows, including how to use the graph-structured skill.

Organize it with concise markdown subsections. Prefer the following subsections when they are useful:
- `### Overview`: briefly state the benchmark and the agent's role.
- `### General Principles`: list concise global rules that should guide all workflows.
- `### Graph-structured Skill Execution Guide`: explain how to execute the skill as a graph: select the relevant task graph using its `Use when` condition, execute the listed node names in order, and apply the instructions under each matching node in `## Node Lists`.

The `### General Principles` subsection should contain portable rules, not a hidden workflow. Put step-by-step procedures, search actions, computations, validations, and recovery routines into `## Node Lists` nodes, then connect them in `## Task Graphs`.

The graph-execution guide should be short and explicit. It may state that:
- `## Global Guidance` applies across all nodes and workflows;
- `## Node Lists` defines reusable execution steps;
- `## Task Graphs` chooses and orders those steps for each task type;
- a numbered workflow should use `1. A`, `2. B`, `3. C` formatting, where `A`, `B`, and `C` are exact node names in execution order.


### `## Node Lists`
This section defines the node library. Each node is a reusable step that can appear in one or more workflows inside the task graphs.

Organize it as:
- one markdown heading per node, for example `### Parse Request`, `### Gather Evidence`, or `### Verify Answer`;
- under each node heading, concise bullets with instructions the agent should follow while executing that node;

Effective nodes should:
- have short, action-oriented names that can be referenced exactly from task graphs;
- represent reusable subtasks, reasoning steps, tool-use steps, validation steps, or recovery strategies;
- be specific enough to guide behavior, but general enough to transfer across benchmark instances;
- separate distinct responsibilities when the order matters, such as parsing the goal, locating evidence, computing, and validating;

Avoid nodes that are empty, redundant, purely decorative, or tied to a single example. Do not create a long block of prose under one node when several reusable nodes would make the graph clearer.

### `## Task Graphs`
This section defines task graphs as collections of workflows, where each workflow is an executable path made from node names in `## Node Lists`.

Organize it as one or more task-type subsections:
- each task graph should have a heading such as `### Direct Evidence Question` or `### Multi-Step Calculation`;
- include a `**Use when:**` line describing when that workflow applies;
- include a `**Workflow:**` block formatted as `1. A`, `2. B`, `3. C`, where `A`, `B`, and `C` are exact node names from `## Node Lists`;
- each numbered item should be an exact node name from `## Node Lists`;

Maintain graph consistency:
- every node referenced in `## Task Graphs` must appear as a node heading in `## Node Lists`;
- node names must match exactly between node headings and graph paths;
- every retained node should be useful for at least one task graph or clearly reusable;
- task graph paths should be ordered, executable, and non-contradictory.


Return JSON only:
{"skills": ["full skill document", "..."]}
