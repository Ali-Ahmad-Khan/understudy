#!/usr/bin/env bash
# Understudy one-command bootstrap. Read me before piping — I'm 40 lines.
#
#   curl -fsSL https://raw.githubusercontent.com/Ali-Ahmad-Khan/understudy/main/setup.sh | bash -s -- claude .
#   curl -fsSL .../setup.sh | bash -s -- cursor ~/code/my-app
#   curl -fsSL .../setup.sh | bash               # defaults: claude target, current dir
#
# What it does — exactly two things:
#   1. Fetch the kit into ${XDG_DATA_HOME:-~/.local/share}/understudy
#      (git clone if available, tarball otherwise; pull --ff-only on re-run).
#   2. Run install.sh <target> <dir> from there, which writes ONLY inside
#      the target project. No global agent config (~/.claude, ~/.cursor,
#      ~/.gemini, AGENTS.md, CLAUDE.md) is ever created or modified.
#
# Overrides: UNDERSTUDY_REPO (source URL or local path), UNDERSTUDY_HOME (cache dir).
set -euo pipefail

REPO="${UNDERSTUDY_REPO:-https://github.com/Ali-Ahmad-Khan/understudy}"
KIT="${UNDERSTUDY_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/understudy}"

if [ -d "$KIT/.git" ]; then
  git -C "$KIT" pull -q --ff-only 2>/dev/null || echo "setup: could not update $KIT — using existing copy" >&2
elif [ -f "$KIT/install.sh" ]; then
  : # non-git copy already present — use as-is
elif command -v git >/dev/null 2>&1; then
  git clone -q --depth 1 "$REPO" "$KIT"
else
  mkdir -p "$KIT"
  curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$KIT" --strip-components=1
fi

[ -f "$KIT/install.sh" ] || { echo "setup: fetch failed — $KIT has no install.sh" >&2; exit 1; }

[ $# -eq 0 ] && set -- claude .
exec bash "$KIT/install.sh" "$@"
