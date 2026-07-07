#!/usr/bin/env python3
"""Cross-platform Understudy installer — the single implementation behind
setup.sh (macOS/Linux), setup.ps1 (Windows), and install.sh. Python 3.9+,
stdlib only.

Usage: python3 install.py <claude|global|cursor|agents|prompt> [target-dir] [--force]

  claude  per-project: doctrine skill + runtime gates (Stop + PostToolUse
          hooks) + project settings (printed, not merged, if
          .claude/settings.json exists)
  global  same enforcement for EVERY Claude Code project on this machine:
          gates in ~/.claude/understudy/, hooks in ~/.claude/settings.json
          (printed, not merged, if it exists). Session state stays in
          ~/.claude — never written into the projects being worked on.
  cursor  doctrine as an always-on project rule (.cursor/rules/)
  agents  doctrine as UNDERSTUDY.md + include line for AGENTS.md harnesses
  prompt  doctrine body to stdout, for any system prompt

Project targets write ONLY inside the target directory; the global target
writes ONLY under ~/.claude. In every mode, existing files are never edited —
where one exists (settings.json, a symlinked skills dir), the needed change
is printed for you instead.
"""

import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
USAGE = "usage: install.py <claude|global|cursor|agents|prompt> [target-dir] [--force]"


def die(msg: str, code: int = 1) -> None:
    print(f"install: {msg}", file=sys.stderr)
    sys.exit(code)


def write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        die(f"{path} exists — pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def hooks_config(script_prefix: str) -> str:
    # Exec form: no shell tokenization, identical under Git Bash and
    # PowerShell; ${CLAUDE_PROJECT_DIR} expands on every OS. Interpreter name
    # chosen for the machine we're installing on. Project installs use the
    # ${CLAUDE_PROJECT_DIR} placeholder; global installs bake the absolute
    # path (exec form guarantees expansion only for the documented placeholder).
    py = "python" if platform.system() == "Windows" else "python3"

    def hook(script: str) -> dict:
        return {"type": "command", "command": py,
                "args": [f"{script_prefix}/{script}"]}

    return json.dumps({"hooks": {
        "PostToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
                         "hooks": [hook("gate_edit.py")]}],
        "Stop": [{"hooks": [hook("gate_stop.py")]}],
    }}, indent=2) + "\n"


GATE_SOURCES = ("gates/gate_edit.py", "gates/gate_stop.py", "sloplint/sloplint.py")


def install_runtime(runtime: Path, force: bool) -> None:
    """Gates + linter + a .gitignore keeping session state out of version control."""
    for rel in GATE_SOURCES:
        src = HERE / rel
        write(runtime / src.name, src.read_text(encoding="utf-8"), force)
    write(runtime / ".gitignore", "state/\n", force)


def wire_settings(settings: Path, script_prefix: str, force: bool) -> None:
    """Create settings with hooks, or print the fragment if settings exist."""
    if settings.exists():
        print(f"note: {settings} exists — add the following hooks to it manually:")
        print(hooks_config(script_prefix), end="")
    else:
        write(settings, hooks_config(script_prefix), force)


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]
    if not args:
        die(USAGE, 2)
    target, dest_arg = args[0], (args[1] if len(args) > 1 else ".")

    doctrine_path = HERE / "DOCTRINE.md"
    if not doctrine_path.exists():
        die("DOCTRINE.md not found next to installer")
    doctrine = doctrine_path.read_text(encoding="utf-8")

    if target == "prompt":
        sys.stdout.write(doctrine)
        return

    skill_md = ("---\n"
                "name: understudy\n"
                "description: Senior-agent operating contract (Understudy). Runtime "
                "gates enforce the [G]-tagged rules; load this at session start so "
                "you know the contract before the gates apply it.\n"
                "---\n\n" + doctrine)

    if target == "global":
        home = Path.home()
        runtime = home / ".claude" / "understudy"
        install_runtime(runtime, force)
        wire_settings(home / ".claude" / "settings.json", runtime.as_posix(), force)

        skills = home / ".claude" / "skills"
        if skills.is_symlink():
            # Symlinked skills dirs belong to the user's own system — writing
            # through one would modify their canonical location uninvited.
            print(f"note: {skills} is a symlink into your own setup — not writing "
                  f"through it. To add the doctrine skill, place this yourself:")
            print(f"  {runtime / 'SKILL.md'}  →  <your skills dir>/understudy/SKILL.md")
            write(runtime / "SKILL.md", skill_md, force)
        else:
            write(skills / "understudy" / "SKILL.md", skill_md, force)
        print("note: global gates now apply to every Claude Code project on this "
              "machine. If a project also has a per-project install, both gates "
              "run — harmless, but pick one scope.")
        return

    dest = Path(dest_arg).resolve()
    if not dest.is_dir():
        die(f"no such directory: {dest_arg}")

    if target == "claude":
        install_runtime(dest / ".claude" / "understudy", force)
        write(dest / ".claude" / "skills" / "understudy" / "SKILL.md", skill_md, force)
        wire_settings(dest / ".claude" / "settings.json",
                      "${CLAUDE_PROJECT_DIR}/.claude/understudy", force)
        print("note: for always-on doctrine, add to the project's CLAUDE.md or AGENTS.md:")
        print("  @.claude/skills/understudy/SKILL.md")

    elif target == "cursor":
        write(dest / ".cursor" / "rules" / "understudy.mdc",
              "---\ndescription: Senior-agent operating contract (Understudy)\n"
              "alwaysApply: true\n---\n\n" + doctrine, force)
        print("note: no hook runtime on this harness — gate output in CI instead:")
        print("  python3 sloplint/sloplint.py <agent-output-file>")

    elif target == "agents":
        write(dest / "UNDERSTUDY.md", doctrine, force)
        print("note: add this line to the project's AGENTS.md to activate:")
        print("  @UNDERSTUDY.md")
        print("note: no hook runtime on this harness — gate output in CI instead:")
        print("  python3 sloplint/sloplint.py <agent-output-file>")

    else:
        die(USAGE, 2)


if __name__ == "__main__":
    main()
