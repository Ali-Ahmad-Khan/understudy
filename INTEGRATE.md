# Agent-driven integration

For setups too particular for a generic installer — global `AGENTS.md`
constitutions, `CLAUDE.md` one-line shims, symlinked skills directories,
memory vaults, pre-existing hooks. Instead of `setup.sh` guessing, your own
agent (Claude Code, Cursor, Antigravity, anything that can read files and run
commands) audits **your** setup and integrates Understudy around it without
touching any of it.

Copy everything inside the block below, paste it into your agent in the
project where you want Understudy active, and review its plan before saying
"go".

---

```text
You are integrating "Understudy" (https://github.com/Ali-Ahmad-Khan/understudy)
— an enforcement harness for agent discipline: a runtime stop-gate + edit/exec
ledger (Claude Code hooks), a deterministic output linter (sloplint), a ~500-word
doctrine, and 5 evaluation drills — into MY existing agent ecosystem. Proceed in
three phases. Do not skip the audit and do not merge phases.

PHASE 1 — AUDIT (strictly read-only; no writes, no installs):
Map my setup and report it back to me compactly:
 1. Which harness(es) am I running you in, and which others are configured on
    this machine/project? (Claude Code, Cursor, Antigravity/Gemini, Codex, ...)
 2. Instruction surfaces: global and project AGENTS.md; CLAUDE.md — and whether
    it is a real file, an @-include shim, or a symlink (report what it points to,
    do NOT dereference-and-edit); .cursor/rules/; GEMINI.md; anything similar.
 3. Skills/rules directories and whether any are symlinked (e.g. ~/.claude/skills
    → elsewhere). Symlinked directories are OFF-LIMITS for writes.
 4. Existing hooks: project and user settings.json (Claude Code), any hook
    scripts already wired. Note exact matchers already in use.
 5. Memory/state systems: .memory/ vaults, MEMORY.md indexes, or similar.
 6. Anything else a new tool could collide with (pre-commit hooks, CI that
    lints markdown, dotfile managers that own these paths).

PHASE 2 — PLAN (still no writes). Propose the minimal integration and WAIT for
my approval. Constraints, non-negotiable:
 - Everything project-local. Never create or modify files under ~/ or any
    global config, even where my setup keeps its canonical files there.
 - Never modify, move, rename, or overwrite ANY existing file. Additions only.
    Where activation requires one include line in an existing file (AGENTS.md /
    CLAUDE.md), show me the exact line and the exact file — I will add it, or
    you add it only after I explicitly approve that single edit.
 - If .claude/settings.json already exists, do NOT merge hooks into it
    yourself; show me the hooks JSON fragment from the Understudy installer and
    where it goes. If my existing hooks already match Edit/Write/Bash or Stop,
    call out the interaction explicitly.
 - Fetch the kit via: git clone --depth 1 the repo above into a scratch or
    vendor location I approve, then use its installer — python3 install.py
    <target> <project> on any OS (./install.sh is the macOS/Linux wrapper;
    targets: claude = doctrine + gates + hooks; cursor / agents = doctrine
    only; prompt = stdout). Prefer the installer over hand-copying.
 - If my setup has its own constitution (AGENTS.md), the Understudy doctrine is
    SUBORDINATE to it: propose wiring it as an on-demand skill or a project
    include, not as a competing global constitution.

PHASE 3 — EXECUTE AND VERIFY (only after my approval):
 1. Run the approved steps exactly; nothing beyond them.
 2. Verify mechanically, not by assertion:
    - python3 <kit>/sloplint/test_sloplint.py  and  python3 <kit>/gates/test_gates.py
      both print "ok".
    - If hooks were installed: simulate one blocked stop — pipe a synthetic
      Stop-hook JSON (session_id, cwd, transcript_path to a fixture transcript
      whose last assistant message is "Great question! Fixed — should work now.
      Want me to continue?") into .claude/understudy/gate_stop.py and confirm
      exit code 2.
    - Diff-check: confirm via git status / find -newer that no pre-existing
      file changed.
 3. Report: what was added (full paths), what I still need to do by hand (the
    include line, the hooks fragment), and the verification output — quoted,
    not summarized.

If any step conflicts with something you found in the audit, stop and ask
rather than improvising around it.
```
