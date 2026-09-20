# ALFWorld Embodied Agent Skill

## Global Guidance

### Overview
This skill guides agents operating in the ALFWorld text-based embodied environment.
The agent must complete household tasks by navigating rooms, interacting with objects,
and using appliances. Actions must be chosen from the admissible action list provided
at each step.

### General Principles

- **Premature termination**: Do not stop the episode until all goal conditions are verified as met.
- **Track progress**: Maintain an internal count of how many objects still need to be found and placed. Only stop searching when the count reaches zero.
- **Avoid loops**: Never repeat the same action more than twice in a row. If stuck, move to a different unexplored location.
- **Only choose admissible actions**: Always pick an action from the admissible action list. Do not invent actions.
- **Decompose the task**: Parse the goal into ordered sub-goals (locate, acquire, transform, deliver). Complete each before moving to the next.
- **Output format**: Always output `<think>...</think>` for reasoning, then `<action>...</action>` for the chosen action.

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

### Parse Goal

### Explore Object
- **Systematic exploration**: Search each surface and container exactly once before revisiting. Open closed containers (drawers, cabinets, fridge) before judging them empty.
- Keep track of which surfaces/containers have been checked; do not re-examine them.

### Take Object
- **Grab immediately**: When a required object is visible and reachable, take it right away before moving elsewhere.
- If the target object appears in the observation, pick it up immediately.

### Find Required Tool or Appliance
- If the task is to examine an object in light, find a desklamp.
- If the task requires cleaning an object, find a sink.
- If the task requires heating an object, find a microwave.
- If the task requires cooling an object, find a fridge.

### Use Desklamp

### Clean, Heat, or Cool
- **Transform before placing**: If the task requires cleaning, heating, or cooling, perform the state change at the appropriate appliance before heading to the final destination.
- Apply the required transformation to the held target object: clean at a sink, heat in a microwave, or cool in a fridge.

### Find Destination Receptacle

### Place Object
- **Direct delivery**: Once holding the transformed (or untransformed) goal object, navigate straight to the target receptacle and place it.

### Verify Completion


---

## Task Graphs

### Pick & Place
**Use when:** Put one requested object in or on the requested receptacle

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Destination Receptacle
5. Place Object
6. Verify Completion

### Pick Two & Place
**Use when:** Put two instances of the requested object in or on the requested receptacle

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Destination Receptacle
5. Place Object
6. Explore Object
7. Take Object
8. Find Destination Receptacle
9. Place Object
10. Verify Completion

### Examine in Light
**Use when:** Examine the requested object in light

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Required Tool or Appliance
5. Use Desklamp
6. Verify Completion

### Clean & Place
**Use when:** Clean the requested object and put it in or on the requested receptacle

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Required Tool or Appliance
5. Clean, Heat, or Cool
6. Find Destination Receptacle
7. Place Object
8. Verify Completion

### Heat & Place
**Use when:** Heat the requested object and put it in or on the requested receptacle

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Required Tool or Appliance
5. Clean, Heat, or Cool
6. Find Destination Receptacle
7. Place Object
8. Verify Completion

### Cool & Place
**Use when:** Cool the requested object and put it in or on the requested receptacle

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Required Tool or Appliance
5. Clean, Heat, or Cool
6. Find Destination Receptacle
7. Place Object
8. Verify Completion
