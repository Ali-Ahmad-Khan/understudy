# Understudy

**An enforcement harness that makes junior models operate like a senior
agent — because discipline you can't enforce is discipline you don't have.**

Fable-class models weren't built on prompt text, and neither is this. Their
operating discipline lives in two places: **training** (RL on agentic
trajectories — not reproducible from the outside) and **the harness**
(mechanical constraints on the loop — fully reproducible). In Claude Code,
"read before you write" isn't a rule the model follows; it's an edit call
that *fails* if the file wasn't read first. Understudy rebuilds that second
layer for any model you point at it: rules become gates, gates block turns,
and the model learns the behavior because the harness refuses the
alternative.

## Architecture — three layers, weakest last

```
┌─ GATES (runtime enforcement) ─────────────────────────────────────────┐
│ gate_edit.py   PostToolUse hook: ledger of every edit + execution     │
│ gate_stop.py   Stop hook: model tries to end its turn →               │
│                 · sloplint the final message (12 slop signatures)     │
│                 · completion claim + code edits + zero executions     │
│                   since the last edit = turn BLOCKED (exit 2),        │
│                   findings fed back, model must fix the cause         │
├─ EVALS (measurement) ─────────────────────────────────────────────────┤
│ sloplint/      deterministic linter, stdlib-only, CI exit codes       │
│ drills/        5 graded tasks with layered traps — the regression     │
│                suite for "did the discipline actually transfer"       │
├─ CONTRACT (text — deliberately last and smallest) ────────────────────┤
│ DOCTRINE.md    ~470 words. Every rule tagged: [G] gate-enforced,      │
│                [H] harness-enforced, [T] text-only. Text carries      │
│                ONLY what machines can't check.                        │
└───────────────────────────────────────────────────────────────────────┘
```

The token economics follow from the layering: the gates cost **zero context
tokens** (they run outside the model, injecting feedback only on violation),
so the always-on text shrinks to ~470 words — the un-checkable residue (goal
decompilation, autonomy calibration, economy ladder), not exhortations the
gates already enforce.

## Quickstart

```sh
git clone <this repo> && cd understudy

# Full enforcement (Claude Code): doctrine + gates + hook wiring,
# written ONLY inside the target project — never global config
./install.sh claude ~/code/my-app

# Doctrine-only adapters for harnesses without a stable hook runtime
./install.sh cursor ~/code/my-app      # .cursor/rules/, alwaysApply
./install.sh agents ~/code/my-app      # UNDERSTUDY.md + AGENTS.md include line
./install.sh prompt | pbcopy           # raw body for any system prompt

# Gate agent output anywhere (CI, pre-commit, other harnesses)
python3 sloplint/sloplint.py response.md          # human report
some-agent ... | python3 sloplint/sloplint.py --json -   # exit 1 over threshold

# Self-checks
python3 sloplint/test_sloplint.py && python3 gates/test_gates.py
```

What a blocked turn looks like (real gate output):

```
UNDERSTUDY STOP GATE — turn blocked. Fix the cause, not the wording that tripped the pattern:
  - [verification-ledger] completion claim ('fixed') with ZERO commands executed after
    the last code edit (server.ts). Doctrine §7: run the changed code / tests and
    report the observed output — or drop the claim and say plainly what is untested.
  - [sloplint:menu-ending] ends by outsourcing a decision ('would you like...')
  - [sloplint] score 7 > 3
```

The model receives that on its own channel and cannot end the turn until the
cause is fixed. One block per stop cycle (`stop_hook_active` honored), so a
session can never loop.

## What each check is, mechanically

| Check | Mechanism | Doctrine rule it replaces |
|---|---|---|
| Verification ledger | `gate_edit.py` records every `Edit/Write/Bash` event per session; `gate_stop.py` refuses completion vocabulary ("fixed", "done", "verified"…) when code edits have no execution after them. Doc-only edits exempt. | "Verify before you claim" — now illegal rather than requested |
| Slop lint | 12 weighted regex rules over the final message, code blocks stripped: filler preambles, buried ledes, hedge padding, "should work" claims, menu endings, promise endings, arrow chains, structure ceremony on short answers, option sprawl, closing chrome, emoji confetti | The entire anti-slop table — as code, not as a table the model reads and forgets |
| Read-before-edit | Claude Code's own tool contract | Free — the harness already enforces it |
| Drills 01–05 | Graded tasks with embedded traps (a second bug only code-tracing finds; a fix that demands a before-and-after run; a work log that must be translated for an absent reader) | The un-gateable skills: goal decompilation, evidence-vs-recall, deciding, reporting |

## Using it as an evaluation harness

1. **Baseline** — run the five drills against your model bare; record rubric
   passes and sloplint scores.
2. **Install** — `./install.sh claude <project>` (or doctrine-only adapter).
3. **Re-run** — same drills, same grading. The delta is the evidence, per
   model, that the system earns its footprint.
4. **Regress** — re-run on every model swap; keep `sloplint --json` in CI as
   the permanent mechanical floor.

## Security posture

Hooks execute code on tool events, so the gates are built to be boring:
stdlib-only, no network, no subprocess, read-only analyzers (the ledger
recorder appends to its own state dir and nothing else), never executing or
eval-ing model output, always exiting 0 on their own failure so a broken gate
can't break a session. The installer writes only inside the target project
and **prints** the hook config instead of merging when a `settings.json`
already exists — it never edits a file it didn't create, and never touches
`~/.claude`, `~/.cursor`, or any global config.

## Honest limits

- The gates catch the mechanical failure modes — unverified claims, decision
  outsourcing, generated-shaped filler. Whether a verified fix is the *right*
  fix stays with the drills and your review.
- "An execution ran after the edit" is necessary, not sufficient — a model
  can run `ls` and technically satisfy the ledger. It defeats lazy claims,
  not adversarial ones; adversarial gaming is visible in the transcript.
- Hook enforcement is Claude Code-first because its hook contract (stdin
  JSON, exit 2 blocks, `stop_hook_active`) is documented and stable. Other
  harnesses get the doctrine plus the CI gate until their hook APIs are worth
  targeting.
- A model that ignores standing instructions *and* has no hook runtime gets
  the CI gate only. The floor is real but lower there.

## Provenance

Distilled July 2026 from the [Claude Fable 5 / Mythos 5
announcement](https://www.anthropic.com/news/claude-fable-5-mythos-5),
Anthropic's Fable 5 migration and behavioral guidance, and the observable
mechanics of the Claude Code harness. Not affiliated with or endorsed by
Anthropic.

## License

MIT — see [LICENSE](LICENSE).
