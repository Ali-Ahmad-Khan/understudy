#!/usr/bin/env bash
# Install Understudy into a target project. Single source: DOCTRINE.md +
# gates/ + sloplint/. Writes ONLY inside the target directory — global config
# (~/.claude, ~/.cursor, ~/.gemini) is never touched.
#
# Usage: ./install.sh <claude|cursor|agents|prompt> [target-dir] [--force]
#
#   claude  full enforcement: doctrine skill + runtime gates (Stop +
#           PostToolUse hooks) + project settings (printed, not merged, if
#           .claude/settings.json already exists)
#   cursor  doctrine as an always-on project rule (.cursor/rules/)
#   agents  doctrine as UNDERSTUDY.md + include line for AGENTS.md harnesses
#   prompt  doctrine body to stdout, for any system prompt / API agent
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
doctrine="$here/DOCTRINE.md"
usage() { sed -n 's/^# \(Usage:.*\)/\1/p' "$0"; exit 2; }

target="${1:-}"; dest="${2:-.}"; force="${3:-}"
[ -z "$target" ] && usage
[ -f "$doctrine" ] || { echo "install.sh: DOCTRINE.md not found next to installer" >&2; exit 1; }

if [ "$target" = "prompt" ]; then
  cat "$doctrine"
  exit 0
fi

dest="$(cd "$dest" 2>/dev/null && pwd)" || { echo "install.sh: no such directory: ${2:-.}" >&2; exit 1; }

write() { # write <path>  (content on stdin)
  local path="$1"
  if [ -e "$path" ] && [ "$force" != "--force" ]; then
    echo "install.sh: $path exists — pass --force to overwrite" >&2; exit 1
  fi
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  echo "wrote $path"
}

hooks_json() {
  cat <<'JSON'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/understudy/gate_edit.py\"" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/understudy/gate_stop.py\"" }
        ]
      }
    ]
  }
}
JSON
}

case "$target" in
  claude)
    # Runtime: gates + linter, self-contained under .claude/understudy/
    u="$dest/.claude/understudy"
    write "$u/gate_edit.py"  < "$here/gates/gate_edit.py"
    write "$u/gate_stop.py"  < "$here/gates/gate_stop.py"
    write "$u/sloplint.py"   < "$here/sloplint/sloplint.py"

    # Contract: doctrine as a project skill
    write "$dest/.claude/skills/understudy/SKILL.md" <<EOF
---
name: understudy
description: Senior-agent operating contract (Understudy). The runtime gates in .claude/understudy/ enforce the [G]-tagged rules; load this at session start so you know the contract before the gates apply it.
---

$(cat "$doctrine")
EOF

    # Hook wiring: create settings if absent; never merge into existing ones
    settings="$dest/.claude/settings.json"
    if [ -e "$settings" ]; then
      echo "note: $settings exists — add the following hooks to it manually:"
      hooks_json
    else
      hooks_json | write "$settings"
    fi
    echo "note: for always-on doctrine, add to the project's CLAUDE.md or AGENTS.md:"
    echo "  @.claude/skills/understudy/SKILL.md"
    ;;
  cursor)
    write "$dest/.cursor/rules/understudy.mdc" <<EOF
---
description: Senior-agent operating contract (Understudy)
alwaysApply: true
---

$(cat "$doctrine")
EOF
    echo "note: no hook runtime on this harness — gate output in CI instead:"
    echo "  python3 sloplint/sloplint.py <agent-output-file>"
    ;;
  agents)
    write "$dest/UNDERSTUDY.md" < "$doctrine"
    echo "note: add this line to the project's AGENTS.md to activate:"
    echo "  @UNDERSTUDY.md"
    echo "note: no hook runtime on this harness — gate output in CI instead:"
    echo "  python3 sloplint/sloplint.py <agent-output-file>"
    ;;
  *)
    usage
    ;;
esac
