## Task context for DocVQA

Environment name: docvqa

This environment evaluates a visual document question answering agent.

At rollout time, the agent receives a document image and a question about that document. The skill should help the agent inspect visible document evidence, identify exact spans, numbers, dates, names, table entries, or layout cues, and answer only what is supported by the image.

The skill should discourage inventing content that is not visible. If multiple near-matches are present, it should prefer the answer best supported by the document.

The final response must put the concise answer inside `<answer>...</answer>` tags.
