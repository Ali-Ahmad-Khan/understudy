#!/usr/bin/env python3
"""Cross-platform Understudy installer — the single implementation behind
setup.sh (macOS/Linux), setup.ps1 (Windows), and install.sh. Python 3.9+,
stdlib only.

Usage: python3 install.py <claude|cursor|agents|prompt> [target-dir] [--force]

  claude  doctrine skill + runtime gates (Stop + PostToolUse hooks) +
          project settings (printed, not merged, if .claude/settings.json exists)
  cursor  doctrine as an always-on project rule (.cursor/rules/)
  agents  doctrine as UNDERSTUDY.md + include line for AGENTS.md harnesses
  prompt  doctrine body to stdout, for any system prompt

Writes ONLY inside the target directory. Never creates or modifies global
config (~/.claude, ~/.cursor, ~/.gemini) and never edits an existing file.
"""

import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
USAGE = "usage: install.py <claude|cursor|agents|prompt> [target-dir] [--force]"


def die(msg: str, code: int = 1) -> None:
    print(f"install: {msg}", file=sys.stderr)
    sys.exit(code)


def write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        die(f"{path} exists — pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def hooks_config() -> str:
    # Exec form: no shell tokenization, identical under Git Bash and
    # PowerShell; ${CLAUDE_PROJECT_DIR} expands on every OS. Interpreter name
    # chosen for the machine we're installing on.
    py = "python" if platform.system() == "Windows" else "python3"

    def hook(script: str) -> dict:
        return {"type": "command", "command": py,
                "args": [f"${{CLAUDE_PROJECT_DIR}}/.claude/understudy/{script}"]}

    return json.dumps({"hooks": {
        "PostToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
                         "hooks": [hook("gate_edit.py")]}],
        "Stop": [{"hooks": [hook("gate_stop.py")]}],
    }}, indent=2) + "\n"


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

    dest = Path(dest_arg).resolve()
    if not dest.is_dir():
        die(f"no such directory: {dest_arg}")

    if target == "claude":
        runtime = dest / ".claude" / "understudy"
        for src in (HERE / "gates" / "gate_edit.py",
                    HERE / "gates" / "gate_stop.py",
                    HERE / "sloplint" / "sloplint.py"):
            write(runtime / src.name, src.read_text(encoding="utf-8"), force)

        write(dest / ".claude" / "skills" / "understudy" / "SKILL.md",
              "---\n"
              "name: understudy\n"
              "description: Senior-agent operating contract (Understudy). The runtime "
              "gates in .claude/understudy/ enforce the [G]-tagged rules; load this at "
              "session start so you know the contract before the gates apply it.\n"
              "---\n\n" + doctrine, force)

        settings = dest / ".claude" / "settings.json"
        if settings.exists():
            print(f"note: {settings} exists — add the following hooks to it manually:")
            print(hooks_config(), end="")
        else:
            write(settings, hooks_config(), force)
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
