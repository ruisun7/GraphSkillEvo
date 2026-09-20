## Task context for SearchQA

Environment name: searchqa

This environment evaluates a question answering agent.

At rollout time, the agent receives a CONTEXT containing document passages and a QUESTION. The skill should help the agent read the supplied context carefully, locate the evidence that answers the question, and answer based only on that evidence.

The final response must put a concise answer inside `<answer>...</answer>` tags. The answer inside the tags should usually be a few words or a short phrase. It should not repeat the question or include unnecessary explanation.
