#!/usr/bin/env bash
# Thin POSIX wrapper around the cross-platform installer (install.py owns all
# logic; this only resolves a Python 3 interpreter). Windows: use setup.ps1
# or run install.py directly.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then py=python3
elif command -v python >/dev/null 2>&1; then py=python
else echo "install.sh: Python 3 is required (https://python.org)" >&2; exit 1; fi
exec "$py" "$here/install.py" "$@"
