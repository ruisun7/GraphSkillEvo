## Task context for LiveMathematicianBench

Environment name: livemathematicianbench

This environment evaluates a mathematical reasoning agent on multiple-choice questions.

At rollout time, the agent receives one mathematics question and its answer choices. The skill should help the agent reason carefully about definitions, quantifiers, hypotheses, extremal wording, equality conditions, and possible traps in the choices.

The final response must put only the single choice label inside `<answer>...</answer>` tags, such as `<answer>B</answer>`.
