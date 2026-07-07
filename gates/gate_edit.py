#!/usr/bin/env python3
"""Understudy ledger recorder — Claude Code PostToolUse hook.

Appends one line per edit/exec event to .claude/understudy/state/<session>.jsonl.
The stop gate reads this ledger to decide whether completion claims are backed
by an execution. Read-only with respect to the model's work: it never touches
files, never blocks, never emits output. Always exits 0 — a broken ledger must
not break the session.
"""

import json
import sys
import time
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    entry = None
    if tool in EDIT_TOOLS:
        entry = {"t": "edit", "path": str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")}
    elif tool == "Bash":
        entry = {"t": "exec", "cmd": str(tool_input.get("command", ""))[:160]}
    if entry is None:
        return 0

    entry["ts"] = time.time()
    try:
        state_dir = Path(data.get("cwd", ".")) / ".claude" / "understudy" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        session = str(data.get("session_id", "unknown")).replace("/", "_")
        with open(state_dir / f"{session}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
