#!/usr/bin/env python3
"""Understudy stop gate — Claude Code Stop hook.

Runs when the model tries to end its turn. Two mechanical checks:

1. sloplint on the final assistant message (doctrine §9 signatures:
   menu/promise endings, unverified-claim phrasing, filler, arrow chains...).
2. Verification ledger: if code files were edited this session and no command
   was executed after the last edit, completion claims ("fixed", "done",
   "verified", ...) in the final message are illegal.

On violation: exit 2 with findings on stderr — Claude Code feeds that back to
the model, which must fix the CAUSE (run the verification, rewrite the
ending) before it is allowed to stop. Loop safety is guaranteed by the gate
itself: it honors stop_hook_active when present AND enforces a hard cap of
BLOCK_CAP blocks per session, so no harness behavior can make it loop
forever.

Security posture: read-only analyzer. Stdlib only, no network, never executes
model output, never modifies files outside its own state dir (which it only
reads here).
"""

import json
import re
import sys
from pathlib import Path

# Windows consoles may default to cp1252; never let an encoding error break a block.
try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Works in both layouts: repo (../sloplint/sloplint.py) and installed
# (sloplint.py copied next to this file by install.sh).
HERE = Path(__file__).resolve().parent
for candidate in (HERE, HERE.parent / "sloplint"):
    if (candidate / "sloplint.py").exists():
        sys.path.insert(0, str(candidate))
        break
from sloplint import lint, score  # noqa: E402

SLOP_THRESHOLD = 3
BLOCK_CAP = 5  # hard per-session ceiling on blocks — the gate's own loop guarantee


def state_dir(cwd: str) -> Path:
    # Mirrors gate_edit.py: installed layout (<anything>/.claude/understudy)
    # keeps state beside the gates (project- or home-local); repo/test layout
    # falls back to the hook's cwd.
    if HERE.name == "understudy":
        return HERE / "state"
    return Path(cwd) / ".claude" / "understudy" / "state"
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".go", ".rs", ".rb",
            ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".bash",
            ".sql", ".php", ".swift", ".kt", ".cs", ".html", ".css", ".vue"}
CLAIM_RE = re.compile(
    r"\b(fixed|done|verified|resolved|works now|now works|passing|passed"
    r"|completed?|implemented|deployed|working as expected)\b", re.I)
# Recognized test/build/run invocations count as verification for any edit.
# ponytail: common-runner list + filename-token fallback; echoing a filename
# into an unrelated command still slips through — that gaming stays visible
# in the transcript.
RUNNER_RE = re.compile(
    r"\b(pytest|unittest|jest|vitest|mocha|rspec|phpunit|ctest|tox"
    r"|npm (test|run|start)|npx |yarn|pnpm|bun|node |deno |tsc\b"
    r"|python3? |ruby |uv run|uvicorn|flask|rails"
    r"|go (test|run|build|vet)|cargo (test|run|build|check)"
    r"|make\b|cmake|mvn|gradle|\./gradlew|dotnet|swift (test|build|run)"
    r"|flutter|docker (build|compose)|curl )", re.I)


def exec_verifies(cmd: str, edit_paths: list) -> bool:
    """A command verifies the edits if it's a recognized runner or names one
    of the edited files (basename or stem)."""
    low = cmd.lower()
    if RUNNER_RE.search(low):
        return True
    for p in edit_paths:
        name = Path(p).name.lower()
        stem = Path(p).stem.lower()
        if (name and name in low) or (len(stem) >= 3 and stem in low):
            return True
    return False


def last_assistant_text(transcript_path: str) -> str:
    """Last assistant message's text blocks from a Claude Code JSONL transcript."""
    text = ""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                content = (obj.get("message") or {}).get("content") or []
                parts = [b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"]
                if parts:
                    text = "\n".join(parts)
    except OSError:
        pass
    return text


def unverified_claim(cwd: str, session_id: str, final_msg: str) -> str | None:
    """Ledger check: code edits with no execution after them + a completion claim."""
    session = str(session_id).replace("/", "_")
    ledger = state_dir(cwd) / f"{session}.jsonl"
    if not ledger.exists():
        return None
    events = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    code_edit_idx = [i for i, e in enumerate(events)
                     if e.get("t") == "edit" and Path(e.get("path", "")).suffix in CODE_EXT]
    if not code_edit_idx:
        return None
    m = CLAIM_RE.search(final_msg)
    if not m:
        return None
    edit_paths = [events[i].get("path", "") for i in code_edit_idx]
    edited = sorted({Path(p).name for p in edit_paths})
    execs_after = [e.get("cmd", "") for e in events[code_edit_idx[-1] + 1:]
                   if e.get("t") == "exec"]
    if not execs_after:
        return (f"completion claim ('{m.group(0)}') with ZERO commands executed after "
                f"the last code edit ({', '.join(edited[:5])}). Run the changed code / "
                f"tests and report the observed output — or drop the claim and say "
                f"plainly what is untested and why.")
    if any(exec_verifies(c, edit_paths) for c in execs_after):
        return None
    return (f"completion claim ('{m.group(0)}') but none of the {len(execs_after)} "
            f"command(s) run after the last code edit look related to the edited "
            f"files ({', '.join(edited[:5])}). Run the changed code or its tests — "
            f"or drop the claim and say plainly what is untested and why.")


def block_count(cwd: str, session_id: str, increment: bool = False) -> int:
    """Per-session block counter — read, optionally increment. Never raises."""
    session = str(session_id).replace("/", "_")
    counter = state_dir(cwd) / f"{session}.blocks"
    try:
        count = int(counter.read_text()) if counter.exists() else 0
    except (OSError, ValueError):
        count = 0
    if increment:
        try:
            counter.parent.mkdir(parents=True, exist_ok=True)
            counter.write_text(str(count + 1))
        except OSError:
            pass
    return count


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    # One enforcement pass per stop cycle when the harness reports it...
    if data.get("stop_hook_active"):
        return 0
    # ...and a hard per-session cap regardless of harness behavior.
    if block_count(data.get("cwd", "."), data.get("session_id", "unknown")) >= BLOCK_CAP:
        return 0

    final_msg = last_assistant_text(data.get("transcript_path", ""))
    if not final_msg.strip():
        return 0

    problems = []

    claim = unverified_claim(data.get("cwd", "."), data.get("session_id", "unknown"), final_msg)
    if claim:
        problems.append(f"[verification-ledger] {claim}")

    findings = lint(final_msg)
    total = score(findings)
    if total > SLOP_THRESHOLD:
        for f in sorted(findings, key=lambda f: -f["weight"])[:6]:
            problems.append(f"[sloplint:{f['rule']}] {f['message']} — \"{f['excerpt']}\"")
        problems.append(f"[sloplint] score {total} > {SLOP_THRESHOLD}")

    if not problems:
        return 0

    block_count(data.get("cwd", "."), data.get("session_id", "unknown"), increment=True)
    sys.stderr.write(
        "UNDERSTUDY STOP GATE — turn blocked. Fix the cause, not the wording that "
        "tripped the pattern:\n" + "\n".join(f"  - {p}" for p in problems) +
        "\nThen rewrite your final message (outcome first, self-contained, no "
        "menus or promises) and end the turn.\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
