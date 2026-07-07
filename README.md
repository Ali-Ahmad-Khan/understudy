# Understudy

**A mentorship kit that makes junior models operate like a senior agent —
with a way to prove it worked.**

Most "agent behavior" repos ship a prompt and hope. Understudy ships a closed
loop: a doctrine the model loads (theory), drills that exercise each behavior
(practice), and a deterministic linter that grades the output (measurement).
Instruction → exercise → measurable check, bound together — that's the
difference between telling a model to be good and training a harness you can
regress-test.

```
 DOCTRINE.md ──installed via──▶ install.sh ──▶ Claude Code / Cursor / AGENTS.md / raw prompt
     │                                              │
     │  each § maps to…                             ▼
     ▼                                    junior model's output
 drills/01–05  ──run task, capture──▶ response.md
                                                │
                                                ▼
                                    sloplint/sloplint.py  → score, exit code
                                    (doctrine §9 + §10 as executable checks)
```

## Why this exists

Claude Fable 5 (Anthropic's Mythos-class model, June 2026) demonstrated that
the gap between frontier output and generic AI output is mostly *operating
discipline*, not raw capability: give it a bare goal and it derives the spec,
works from evidence gathered in-session, verifies before claiming, decides
instead of enumerating, and reports outcome-first. Anthropic's own migration
guidance shows these behaviors are largely *elicitable in smaller models with
the right standing instructions*. Understudy distills that discipline into a
portable doctrine and — because instructions drift and models regress — pairs
it with a mechanical way to check compliance.

## Quickstart

```sh
git clone <this repo> && cd understudy

# 1. Install the doctrine into a project (writes ONLY inside that project)
./install.sh cursor  ~/code/my-app     # .cursor/rules/understudy.mdc (always-on)
./install.sh claude  ~/code/my-app     # .claude/skills/understudy/SKILL.md
./install.sh agents  ~/code/my-app     # UNDERSTUDY.md + one include line
./install.sh prompt | pbcopy           # raw body for any system prompt / API agent

# 2. Grade any agent response — no dependencies, Python 3.9+
python3 sloplint/sloplint.py response.md
some-agent --task "..." | python3 sloplint/sloplint.py --json -

# 3. Run the curriculum: give a drill's task to your model, grade against
#    its rubric, sloplint the response
open drills/01-goal-decompilation.md
```

## The parts

| Part | What it is | Why it's here |
|---|---|---|
| [`DOCTRINE.md`](DOCTRINE.md) | ~1.9k-token operating doctrine, second person, harness-agnostic. Stance → loop → goal decompilation → evidence → decision → economy → autonomy → verification → reporting → anti-slop table → pre-return checklist → safety floor. | The single source. Every adapter is stamped from this file; edit it once, reinstall everywhere. |
| [`install.sh`](install.sh) | Zero-dependency installer: `claude`, `cursor`, `agents`, `prompt` targets. Refuses to overwrite without `--force`. Never touches global config. | Reproducible deployment at scale — same doctrine, correct frontmatter per harness, project-local only. |
| [`sloplint/`](sloplint/) | Stdlib-only Python linter (~200 lines) implementing doctrine §9/§10 as 12 weighted rules: filler preambles, buried ledes, hedge padding, unverified claims ("should work"), menu endings, promise endings, arrow chains, structure ceremony on short answers, option sprawl, closing chrome, emoji confetti. Code blocks are exempt. JSON output, exit codes for CI. | Deterministic measurement. Same text → same score, so you can gate CI on agent output or A/B doctrine-on vs doctrine-off with numbers instead of vibes. |
| [`drills/`](drills/) | Five graded exercises, one per load-bearing doctrine section: goal decompilation, evidence vs. recall, decide-don't-enumerate, verify-before-claim, report-for-the-absent-reader. Each ships the exact task prompt, a pass rubric, the slop tells, and which sloplint rules auto-catch failures. Drills 02 and 04 embed layered traps (a second bug only code-tracing finds; a fix that needs a before-and-after run). | The practice layer — and your regression suite when you swap models. A model that passes all five with clean sloplint scores has demonstrably absorbed the doctrine, not just loaded it. |

## Using it as an evaluation harness

The intended workflow for teams running smaller/cheaper models:

1. **Baseline** — run the five drills against your model *without* the
   doctrine; save responses, record sloplint scores and rubric passes.
2. **Install** — add the doctrine via `install.sh` (or system prompt).
3. **Re-run** — same drills, same grading. The delta is your evidence the
   doctrine earns its ~1.9k tokens for that model. No delta → your model
   ignores standing instructions and needs a different intervention.
4. **Regress** — re-run on every model swap or prompt change. Wire
   `sloplint --json` into CI for the mechanical half.

## Design principles

- **Deterministic first.** The grader is regex and arithmetic, not an
  LLM-judge — free, instant, and identical on every run. LLM judgment stays
  where it belongs: the human-graded halves of the drill rubrics.
- **One source, stamped adapters.** No per-harness forks of the doctrine to
  drift apart; `install.sh` generates them.
- **Project-local, never global.** The installer writes only inside the
  target directory. Your machine-level agent setup is not its business.
- **Zero dependencies.** Bash + Python stdlib. Nothing to `pip install`,
  nothing to break.
- **Checkable over aspirational.** Every doctrine rule is phrased so a reader
  (or the linter) can answer "did the output comply?" with yes or no.

## Limits, honestly

`sloplint` catches the *mechanical* slop signatures — the shape of generated
filler. It cannot verify that a claim is actually evidenced or that a
decision is right; that's what the drill rubrics and your own review are for.
The doctrine raises the floor of models that follow standing instructions
well; it cannot add capability a model doesn't have.

## Provenance

Distilled July 2026 from the [Claude Fable 5 / Mythos 5
announcement](https://www.anthropic.com/news/claude-fable-5-mythos-5),
Anthropic's published Fable 5 migration and behavioral guidance, and observed
Fable operating behavior. Not affiliated with or endorsed by Anthropic.

## License

MIT — see [LICENSE](LICENSE).
