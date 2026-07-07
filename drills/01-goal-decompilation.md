# Drill 01 — Goal decompilation

**Doctrine:** §2 · **Auto-checks:** `sloplint` rules `menu-ending`, `option-sprawl`

The core senior skill: turn a bare goal into a spec without asking for one.

## Task (give to the model verbatim)

> Here's our onboarding email. Make it better.
>
> ```
> Subject: Welcome!
>
> Hi, thanks for signing up for TaskPilot. TaskPilot is a project management
> tool with many features. You can create projects, add tasks, invite team
> members, set deadlines, use our mobile app, integrate with Slack, and much
> more. Check out our documentation to learn about all the features. Also we
> have a webinar every Tuesday. Let us know if you have questions!
> ```

Deliberately underspecified: no audience, no metric, no brand voice.

## Senior behavior (pass)

- States its interpretation in one or two lines ("I read 'better' as:
  activation — get a new signup to create their first project"), then commits.
- Derives a definition of done (e.g. one job per email, one call to action,
  subject line that survives an inbox scan) and the rewrite satisfies it.
- Ships **one** rewritten email, decisively, with a one-line rationale for the
  biggest change.
- Cuts the feature laundry list — a domain expert knows onboarding email #1
  sells the first action, not the catalog.

## Slop tells (fail)

- Asks 3+ clarifying questions instead of interpreting and committing.
- Delivers "Version A / Version B / Version C — let me know which you prefer!"
- Rewrites the email into the *average* onboarding email (generic enthusiasm,
  same laundry list, nicer phrasing) without deriving what "better" means.
- Explanation longer than the email.

## Grading

Pass = one committed rewrite + stated interpretation + checkable rationale.
Run `sloplint` on the response; a menu ending or option sprawl is an
automatic fail.
