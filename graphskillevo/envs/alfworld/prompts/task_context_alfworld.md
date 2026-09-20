## Task context for ALFWorld

Environment name: alfworld

This environment evaluates an agent operating step by step in the ALFRED Embodied Environment.

At rollout time, each step provides the stable task goal, the current observation, and the currently admissible actions. Some rollouts also include recent observation/action history or retrieved experience. The skill should help the agent maintain progress toward the task goal, interpret the current state, choose useful exploration or manipulation actions, and avoid repeating unproductive actions.

At each rollout step, the agent must reason inside `<think>...</think>` tags and then choose exactly one admissible action inside `<action>...</action>` tags.
