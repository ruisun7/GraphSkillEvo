For theorem-grounded mathematical multiple-choice questions, analyze failed trajectories by comparing the predicted option with the correct option. Use this analysis to guide how the skill should be revised; do not merely paste task-solving rules into the skill.

Failure type categories:
- **quantifier_miss**: missed exact quantifiers, scope, existence, uniqueness, or universality.
- **strength_mismatch**: selected a statement weaker or stronger than what the theorem or question asks for.
- **condition_miss**: ignored hypotheses, equality cases, edge cases, or domain restrictions.
- **option_confusion**: confused similar choices or failed to compare answer-choice wording exactly.
- **other**: none of the above.

Analysis and revision process:
1. Read all failed trajectories before revising the skill.
2. Compare predicted option text and correct option text, not only option labels.
3. Look for repeated mismatch patterns across several failures, especially:
   - a concrete answer choice when the correct answer is a stronger meta-option;
   - a weaker or stronger statement when the question asks for the exact strength;
   - a missing quantifier, condition, equality case, or domain restriction;
   - two similar-looking options that differ in one crucial phrase.
4. When failures involve strongest-statement, equivalence, or complete-classification questions with a meta-option, diagnose whether the current skill lacks a calibrated maximality-certification procedure. Good revisions should make the target agent compare concrete options against the meta-option using option-text evidence, including quantifier scope, implication/equivalence arrows, endpoints and regimes, asymptotic or quantitative form, extra structural add-ons, and constant or parameter dependence.
5. Turn repeated patterns into label-invariant decision procedures. Phrase revisions as general mechanisms for exact option discrimination, not as theorem facts or fixed answer priors.
6. If the mutation target is graph structure, prefer explicit reusable decision nodes for missing checks, such as meta-option detection, maximality certification, and strength-switch auditing. Route strongest-statement, equivalence, complete-classification, theorem-precision, and close-option-comparison workflows through those nodes before final answer selection.
7. New graph nodes must change the decision path or add a required discrimination check. Do not add generic parse, reread, verify, or be-careful nodes unless they force a concrete option-comparison action.
8. If an existing rule was ignored, prefer strengthening the relevant node or rerouting workflows through it rather than duplicating the same advice elsewhere.
9. Do not copy task IDs, fixed option letters, gold answers, or paper-specific facts into the skill. Keep the revision concise and integrated with the existing guidance instead of appending a long standalone block.