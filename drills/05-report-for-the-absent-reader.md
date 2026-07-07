# Drill 05 — Report for the absent reader

**Doctrine:** §8 · **Auto-checks:** `sloplint` rules `arrow-chain`, `buried-lede`, `structure-overhead`

Can the model translate its own working shorthand into a self-contained
report? Run the output through `sloplint` directly.

## Task (give to the model verbatim)

> You are an engineering agent. Below is your own raw work log from an
> overnight run. Write the message your operator reads in the morning —
> their first look at any of this.
>
> ```
> 22:04 start. ticket: "checkout intermittently 500s"
> 22:10 repro'd: POST /checkout → 500 ~1/20 reqs
> 22:31 traced to inventory svc timeout 200ms, p99 is 340ms since Tue
> 22:58 Tue = deploy of INV-441 (new audit query, unindexed)
> 23:20 plan A: raise timeout → rejected, masks it
> 23:41 added index CONCURRENTLY on audit_events(order_id) in staging
> 00:15 staging p99 → 38ms. 500s gone over 2k requests
> 00:20 prod index NOT applied — needs approval per runbook
> 00:22 wrote runbook entry + rollback note
> ```

## Senior behavior (pass)

- First sentence is the outcome and the one thing needing action: root cause
  found and fix verified in staging; **prod index application awaits their
  approval**.
- Complete sentences; the reader never sees `→`, `repro'd`, `p99` without a
  gloss, or "plan A" (a label from the log they never saw).
- Selective: the 22:31/22:58 causal chain survives (it changes what the
  reader approves); timestamps and the rejected-plan detour compress to a
  clause or vanish.
- The approval ask is unmissable, not buried in paragraph three.

## Slop tells (fail)

- Chronological replay of the log ("At 22:04 I started…").
- Log shorthand pasted through: arrow chains, "plan A", bare metric jargon.
- Buries "needs your approval" under a `## Next Steps` header at the bottom.
- Header-and-bullet ceremony on what should be two short paragraphs.

## Grading

Pass = outcome + ask in the first two sentences, zero invented labels, and
`sloplint` scores 0. This is the one drill where the linter alone catches
most failures.
