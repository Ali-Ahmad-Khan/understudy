# Drill 03 — Decide, don't enumerate

**Doctrine:** §4 · **Auto-checks:** `sloplint` rules `option-sprawl`, `menu-ending`, `structure-overhead`

A question with a clearly correct answer, phrased to bait a comparison essay.

## Task (give to the model verbatim)

> We're building a single-user desktop note-taking app in Electron. Notes are
> plain text, a few thousand at most. Should we use SQLite or Postgres for
> storage? Give us your take.

The evidence settles this: single-user, local, embedded, tiny data → SQLite
(arguably even flat files — a model that notices *that* and says so in one
line is performing above the bar, not below it).

## Senior behavior (pass)

- Direct answer in the first sentence: SQLite.
- One or two lines of why (embedded, zero-ops, single-writer is exactly its
  design center; Postgres means running a server for one user).
- At most one sentence on when to revisit (sync/multi-device later).
- Total length: a short paragraph. No headers, no table.

## Slop tells (fail)

- A comparison table or symmetric pros/cons list for a question that isn't
  close.
- "It depends on your needs…" followed by both options kept alive.
- Ends with "Would you like me to elaborate on either option?"
- 400 words with headers for a one-paragraph answer.

## Grading

Pass = verdict in sentence one, prose-only, under ~120 words. `sloplint`
should score 0.
