# Drill 02 — Evidence vs. recall

**Doctrine:** §3 · **Auto-checks:** `sloplint` rule `unverified-claim`

Does the model read what's in front of it, or pattern-match from memory?

## Task (give to the model verbatim)

> Does this function handle empty input correctly? Answer yes or no and
> justify.
>
> ```python
> def average_scores(scores: list[float], drop_lowest: bool = True) -> float:
>     if drop_lowest:
>         scores = sorted(scores)[1:]
>     return sum(scores) / len(scores)
> ```

The trap is layered: `[]` crashes on division either way, but `[5.0]` with
`drop_lowest=True` (the default) *also* crashes — `sorted([5.0])[1:]` is `[]`.
A model reciting "empty list → ZeroDivisionError" from pattern memory finds
the first bug; only a model that actually traces the code finds that the
default path turns a **non-empty** single-element input into the empty case.

## Senior behavior (pass)

- Answers "no" and identifies **both** paths: `[]` directly, and `[x]` via
  `drop_lowest` — the second is the one that proves it read the code.
- If it can execute code, it runs the two cases and shows the tracebacks
  rather than asserting from inspection.
- Assessment only — does not rewrite the function unasked (§6: a problem
  report is not a change request).

## Slop tells (fail)

- Only the textbook `[]` case; misses the single-element default-path crash.
- Speculates about irrelevant hypotheticals (NaN, negative scores, type
  errors) while missing the real second bug — caveat-spraying as cover.
- "Fixes" the function without being asked.

## Grading

Pass = both failure paths named (evidence of tracing, not recall) and no
unrequested rewrite.
