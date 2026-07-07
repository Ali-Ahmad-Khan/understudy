# Drill 06 — Constitutive scope

**Doctrine:** §Anatomy · **Auto-checks:** none (this is the judgment the gates can't check)

The domain-expert behavior: a request names an artifact class; the artifact
has parts the prompt never enumerates. Seniors build from the artifact's
anatomy and cut consciously; juniors build from the prompt's vocabulary and
omit by ignorance.

## Task (give to the model verbatim)

> Design the navigation and page structure for a client portal for my design
> agency. Clients should be able to see the status of their projects and the
> deliverables we've shipped them.

Deliberately narrow: the prompt names only two nouns (status, deliverables).
A real client portal has an anatomy the requester didn't spell out.

## Senior behavior (pass)

- The structure includes constitutive parts the prompt never mentioned,
  because every real client portal has them: somewhere files/documents live,
  billing/invoices, messages or another communication channel, team/access
  management, account settings.
- Each unrequested part is justified in a line grounded in how the artifact
  is actually used ("clients will ask where to pay the invoice — billing is
  not optional in a portal"), not padded in silently.
- Still cuts the merely conceivable — no white-label theming engine, no
  client-facing analytics suite, no plugin system. The additions are anatomy,
  not ambition.
- Omissions are stated as decisions: "No client-side task creation — that's
  your team's surface, not theirs."

## Slop tells (fail)

- Ships exactly the two nouns in the prompt (a status page and a
  deliverables list) and nothing else — prompt-vocabulary design.
- The opposite failure: pads twenty features with no constitutive/conceivable
  line — anatomy and ambition indistinguishable, nothing justified.
- Asks the requester to enumerate what the portal should contain — the
  expertise the model was supposed to supply, outsourced back.
- Every unrequested part appears without a stated reason, so the reviewer
  can't tell knowledge from noise.

## Grading

Pass = at least three constitutive parts beyond the prompt's nouns, each with
a one-line usage-grounded justification, plus at least one explicit stated
omission. Automatic fail if the deliverable contains only what the prompt
named, or if additions appear without justification.
