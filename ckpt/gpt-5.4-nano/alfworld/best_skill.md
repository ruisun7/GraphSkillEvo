# ALFWorld Robust Coverage & Mode-Operation Skill

## Global Guidance

### Overview
This skill guides agents in the ALFWorld embodied text environment to complete household tasks by navigating, interacting with objects/appliances, and delivering results. At every step, only choose an action that is currently admissible.

### General Principles
- **No premature termination**: Do not stop until the goal conditions are satisfied as evidenced in the observation.
- **Track progress**: Maintain an internal counter for how many required object instances still need to be placed/examined correctly; decrement only when the observation confirms success.
- **Avoid loops**: Never repeat the same action more than **twice in a row**. If progress stalls, move to a different room/area or a different target surface/container.
- **Coverage-first exploration**: When searching a room, check each relevant surface/container at most once; open closed containers when appropriate before deciding they’re empty.
- **Admissible actions only**: Always pick from the admissible action list provided at the current step. Do not invent action strings.
- **Decompose the task**: Plan in ordered phases: locate → (optional mode operation) → deliver → verify.
- **Output format**: Always output exactly one admissible action inside `<action>...</action>` and include reasoning inside `<think>...</think>`.

### Graph-structured Skill Execution Guide
Use the graph nodes below as reusable subtasks.
1. Identify the best matching task-type workflow in **Task Graphs** using its **Use when:** condition.
2. Execute the nodes in the listed order (each node may require multiple environment steps until its sub-goal is achieved).
3. For each node, follow the instructions under that node’s heading in **Node Lists**.
4. If a prerequisite is missing (target/tool/destination not confirmed), the relevant node should switch to coverage-based search in new unexplored areas rather than looping.

## Node Lists

### Parse Goal
- Read the stable task goal to extract:
  - target object name(s) and required instance count
  - required operation mode: none / clean / heat / cool / examine-in-light
  - destination receptacle and whether placement must be **in** or **on**
- Decide phase order: **locate → mode operation (if any) → deliver → verify**.
- Initialize internal bookkeeping:
  - `remaining_instances = required_count`
  - `mode_needed = ...`
  - `destination_is_in_or_on = ...` (in/on from goal wording)
  - `target_acquired_count = 0`
  - `destination_verified = false`

### Explore Object
- Purpose: locate target object instance(s) using strict coverage and “no re-checking”.
- Maintain an internal set `checked_surfaces_containers` for the current room/run.
- Coverage rule (must follow):
  - If the current surface/container is already in `checked_surfaces_containers`, **do not** open/examine it again. Immediately navigate to an unvisited candidate surface/container.
  - If a container/surface is closed and potentially relevant, open it **once**, then inspect.
  - Mark the surface/container as checked after you either:
    - observe it does not contain the target, or
    - observe the target is present (in which case you can exit the explore phase for taking).
- Stop exploring when:
  - the observation shows the target object is visible and can plausibly be taken next.
- If progress is blocked (nothing new after checking what’s available):
  - navigate to a **different unexplored area** (do not bounce between the same two surfaces/containers).
- Avoid action repetition:
  - If an examine/open action does not change the observation content, move on (do not re-issue the same examine/open on the same place again).
- If the prerequisite for the upcoming action is now satisfied (e.g., the object becomes visible), transition to the next node’s intent.

### Take Object
- Precondition: `remaining_instances > 0`.
- If the target object is visible and reachable in the current observation:
  - take/grab **one** instance using an admissible take/grab action.
  - confirm success from the observation (e.g., the object is now held/removed from its surface).
  - increment `target_acquired_count` by 1 and **do not** decrement `remaining_instances` until placement/examination confirmation (per global guidance).
- If the target is not visible/reachable:
  - do not repeatedly attempt irrelevant actions.
  - perform short-range, coverage-aware relocation by navigating to a nearby unvisited plausible area (surface/container type diversity), then reassess visibility.
  - once the target becomes visible, take it immediately.

### Find Required Tool or Appliance
- Based on `mode_needed`, search for the correct appliance/tool:
  - **examine-in-light** → desklamp
  - **clean** → sink
  - **heat** → microwave
  - **cool** → fridge
- Use coverage-aware exploration to find and confirm the appliance/tool is visible and accessible.
- If the appliance is not immediately visible:
  - prioritize checking its most likely locations by navigating to those areas rather than looping at unrelated surfaces.

### Use Desklamp
- Position/adjust so the agent can perform the examination under the lamp using admissible lamp-related actions.
- Ensure the observation indicates the object was examined (or that the relevant “in light” event occurred).
- Do not proceed to completion/verify until examination evidence is present.

### Clean, Heat, or Cool
- Handles the full appliance operation so the agent ends this node ready to place the object.
- Preconditions:
  - the target object is currently held (from Take Object) or can be positioned into the appliance using admissible actions.
- Operation mapping:
  - clean → sinkbasin
  - heat → microwave
  - cool → fridge
- Steps:
  1. Move to the correct appliance area (if not already there) using admissible navigation.
  2. Perform only admissible interaction actions to apply the required mode.
  3. Wait/step as needed until the observation indicates the mode state change completed (e.g., “cleaned”, “heated”, “cooled”).
  4. Retrieve the object from the appliance (perform any required admissible open/close/confirm steps) so the agent can carry it to the destination.
- If the mode change is not confirmed:
  - remain in this node and retry operation only with admissible actions.
  - avoid repeating the same unsuccessful interaction more than twice in a row.

### Find Destination Receptacle
- Locate the destination receptacle specified in the goal.
- Identify placement relation **in** vs **on** by matching goal wording.
- Once the receptacle is visible:
  - navigate to a position where placing is possible (close enough to interact).
- Do not place yet; only ensure destination is confirmed and reachable.

### Place Object
- While holding the target object, navigate (if needed) directly to the destination receptacle.
- Place it **in/on** according to `destination_is_in_or_on` using the admissible place/put action.
- After placing, require explicit observational confirmation that:
  - the object is now located in/on the correct receptacle, and
  - any completed mode requirement is satisfied (if the observation mentions cleanliness/temperature/examination).
- Progress accounting:
  - decrement `remaining_instances` only when confirmation is explicit.
- If confirmation is missing:
  - retry placement cautiously without repeating the same place action more than twice in a row.
  - if still not confirmed, reposition around the receptacle within admissible moves and reattempt.

### Verify Completion
- Check the observation for goal satisfaction:
  - correct receptacle placement for all required instances (and correct in/on condition), and/or
  - examination-in-light evidence / mode-change evidence as required by the goal.
- Update `remaining_instances` only when confirmation is explicit.
- If complete:
  - choose an admissible finish/stop-like action if available; otherwise choose an action that doesn’t undo progress.
- If not complete:
  - do **not** terminate.
  - recovery behavior (inside this node):
    1. If `remaining_instances > 0` and the target object is not correctly placed, shift to **Explore Object** for missing instances (prefer unvisited areas).
    2. If the mode requirement is not satisfied for an acquired object, shift to **Find Required Tool or Appliance** and then complete the missing mode before placing again.
    3. If destination is unclear, shift to **Find Destination Receptacle** behavior by navigating to likely destination surfaces/containers.

## Task Graphs

### Pick & Place
**Use when:** Put one instance of the requested object in/on the requested receptacle, with **no** clean/heat/cool/examine requirement.

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Destination Receptacle
5. Place Object
6. Verify Completion

### Pick Two & Place
**Use when:** Put **two** instances of the requested object in/on the requested receptacle.

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Destination Receptacle
5. Place Object
6. Verify Completion

### Examine in Light
**Use when:** Examine the requested object in light (desklamp-based) as required by the goal.

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Required Tool or Appliance
5. Use Desklamp
6. Verify Completion

### Clean & Place
**Use when:** Clean the requested object and then place it in/on the requested receptacle.

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
**Use when:** Heat the requested object and then place it in/on the requested receptacle.

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
**Use when:** Cool the requested object and then place it in/on the requested receptacle.

**Workflow:**
1. Parse Goal
2. Explore Object
3. Take Object
4. Find Required Tool or Appliance
5. Clean, Heat, or Cool
6. Find Destination Receptacle
7. Place Object
8. Verify Completion
