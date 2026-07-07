# Understudy

[![ci](https://github.com/Ali-Ahmad-Khan/understudy/actions/workflows/ci.yml/badge.svg)](https://github.com/Ali-Ahmad-Khan/understudy/actions/workflows/ci.yml)
![platforms](https://img.shields.io/badge/platforms-macOS%20·%20Linux%20·%20Windows-4c8dae)
![deps](https://img.shields.io/badge/dependencies-none%20(stdlib)-2f9e44)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

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

## Setup — one command per OS, one installer underneath

The only hard requirement is **Python 3.9+**. Git is used if present
(tarball/zip fallback otherwise). Every path below ends in the same
cross-platform installer, [`install.py`](install.py), producing identical
artifacts — the generated hooks use Claude Code's *exec form*, which behaves
the same under Git Bash and PowerShell, so there is one wiring, not one per OS.

**macOS / Linux / WSL / Git Bash** — run from inside the project you want gated:

```sh
curl -fsSL https://raw.githubusercontent.com/Ali-Ahmad-Khan/understudy/main/setup.sh | bash
```

**Windows (PowerShell)**:

```powershell
irm https://raw.githubusercontent.com/Ali-Ahmad-Khan/understudy/main/setup.ps1 | iex
```

Both default to full Claude Code enforcement in the current directory. Pick a
target and directory explicitly:

```sh
# macOS/Linux — targets: claude | cursor | agents | prompt
curl -fsSL https://raw.githubusercontent.com/Ali-Ahmad-Khan/understudy/main/setup.sh | bash -s -- cursor ~/code/my-app
```

```powershell
# Windows
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Ali-Ahmad-Khan/understudy/main/setup.ps1))) cursor C:\code\my-app
```

The bootstraps are ~40 readable lines each: fetch the kit once into
`~/.local/share/understudy` (`%LOCALAPPDATA%\understudy` on Windows), then run
`install.py`, which writes **only inside the target project**. Re-running
updates the cache and re-installs. Pipe-to-shell makes you nervous (good
instinct)? Read [`setup.sh`](setup.sh) / [`setup.ps1`](setup.ps1) first, or go manual:

```sh
git clone https://github.com/Ali-Ahmad-Khan/understudy && cd understudy

python3 install.py claude ~/code/my-app   # doctrine + gates + hook wiring  (Windows: python)
python3 install.py cursor ~/code/my-app   # .cursor/rules/, alwaysApply
python3 install.py agents ~/code/my-app   # UNDERSTUDY.md + AGENTS.md include line
python3 install.py prompt                 # doctrine to stdout, for any system prompt

# Gate agent output anywhere (CI, pre-commit, other harnesses)
python3 sloplint/sloplint.py response.md          # human report
some-agent ... | python3 sloplint/sloplint.py --json -   # exit 1 over threshold

# Self-checks (also run in CI on Ubuntu, macOS, and Windows)
python3 sloplint/test_sloplint.py && python3 gates/test_gates.py
```

After a `claude` install, activation is two spots the installer tells you
about: hooks (written for you, or printed if you already have a
`settings.json`) and one optional `@.claude/skills/understudy/SKILL.md`
include line for always-on doctrine.

## Fitting into an ecosystem you already have

Understudy assumes you have a setup it should respect — a global `AGENTS.md`
constitution, a `CLAUDE.md` that is a one-line shim or symlink, skills
directories symlinked across harnesses, a `.memory/` vault, hooks already
wired. Three properties keep it from colliding:

- **Project-local, additive-only.** Every artifact lands inside the target
  project (`.claude/understudy/`, `.claude/skills/understudy/`,
  `.cursor/rules/`, `UNDERSTUDY.md`). Nothing under `~/` is created or
  modified; existing files are never edited — where activation needs one
  include line in *your* `AGENTS.md`/`CLAUDE.md`, the installer prints the
  line and leaves the edit to you.
- **Print, don't merge.** If `.claude/settings.json` already exists, the
  installer prints the hooks JSON fragment instead of touching your file.
- **Subordinate by design.** If you run a constitution, the doctrine slots in
  as a project skill or include under it — it's a contract for the model's
  output discipline, not a competing constitution.

For setups too particular for any generic installer, use
[`INTEGRATE.md`](INTEGRATE.md): a copy-paste prompt that makes **your own
agent** audit your ecosystem (read-only), propose a minimal integration plan,
wait for your approval, then execute and mechanically verify — including a
diff-check that nothing pre-existing changed.

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
