#!/usr/bin/env bash
# Stamp the Understudy doctrine into a target project as a harness adapter.
# Single source: DOCTRINE.md. Writes ONLY inside the target directory —
# never global config (~/.claude, ~/.cursor, ~/.gemini are never touched).
#
# Usage: ./install.sh <claude|cursor|agents|prompt> [target-dir] [--force]
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
doctrine="$here/DOCTRINE.md"
usage() { grep '^# Usage:' "$0" | cut -c3-; exit 2; }

target="${1:-}"; dest="${2:-.}"; force="${3:-}"
[ -z "$target" ] && usage
[ -f "$doctrine" ] || { echo "install.sh: DOCTRINE.md not found next to installer" >&2; exit 1; }

# prompt mode needs no destination — print body to stdout for piping
if [ "$target" = "prompt" ]; then
  cat "$doctrine"
  exit 0
fi

dest="$(cd "$dest" 2>/dev/null && pwd)" || { echo "install.sh: no such directory: ${2:-.}" >&2; exit 1; }

write() { # write <path> <<content-from-stdin>
  local path="$1"
  if [ -e "$path" ] && [ "$force" != "--force" ]; then
    echo "install.sh: $path exists — pass --force to overwrite" >&2; exit 1
  fi
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  echo "wrote $path"
}

case "$target" in
  claude)
    # Project-level Claude Code skill (loads on demand via the Skill tool).
    write "$dest/.claude/skills/understudy/SKILL.md" <<EOF
---
name: understudy
description: Senior-agent operating doctrine (Understudy). Load at session start, or whenever configuring a subagent, to operate goal-first — derive the spec from a bare goal, work on evidence, verify before claiming, decide instead of enumerating, report outcome-first.
---

$(cat "$doctrine")
EOF
    echo "note: for always-on behavior, add this line to the project's CLAUDE.md or AGENTS.md:"
    echo "  @.claude/skills/understudy/SKILL.md"
    ;;
  cursor)
    # Always-on Cursor project rule.
    write "$dest/.cursor/rules/understudy.mdc" <<EOF
---
description: Senior-agent operating doctrine (Understudy)
alwaysApply: true
---

$(cat "$doctrine")
EOF
    ;;
  agents)
    # Neutral file for AGENTS.md-based harnesses (Antigravity, Gemini CLI,
    # Codex, ...). We create a new file and print the include line rather
    # than editing an existing AGENTS.md.
    write "$dest/UNDERSTUDY.md" < "$doctrine"
    echo "note: add this line to the project's AGENTS.md to activate:"
    echo "  @UNDERSTUDY.md"
    ;;
  *)
    usage
    ;;
esac
