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
ending) before it is allowed to stop. Blocks at most once per stop cycle
(honors stop_hook_active), so a session can never loop forever.

Security posture: read-only analyzer. Stdlib only, no network, never executes
model output, never modifies files outside its own state dir (which it only
reads here).
"""

import json
import re
import sys
from pathlib import Path

# Works in both layouts: repo (../sloplint/sloplint.py) and installed
# (sloplint.py copied next to this file by install.sh).
HERE = Path(__file__).resolve().parent
for candidate in (HERE, HERE.parent / "sloplint"):
    if (candidate / "sloplint.py").exists():
        sys.path.insert(0, str(candidate))
        break
from sloplint import lint, score  # noqa: E402

SLOP_THRESHOLD = 3
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".go", ".rs", ".rb",
            ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".bash",
            ".sql", ".php", ".swift", ".kt", ".cs", ".html", ".css", ".vue"}
CLAIM_RE = re.compile(
    r"\b(fixed|done|verified|resolved|works now|now works|passing|passed"
    r"|completed?|implemented|deployed|working as expected)\b", re.I)


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
    ledger = Path(cwd) / ".claude" / "understudy" / "state" / f"{session}.jsonl"
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
    exec_after = any(e.get("t") == "exec" for e in events[code_edit_idx[-1] + 1:])
    if exec_after:
        return None
    m = CLAIM_RE.search(final_msg)
    if not m:
        return None
    edited = sorted({Path(events[i]["path"]).name for i in code_edit_idx})
    return (f"completion claim ('{m.group(0)}') with ZERO commands executed after the "
            f"last code edit ({', '.join(edited[:5])}). Doctrine §7: run the changed "
            f"code / tests and report the observed output — or drop the claim and say "
            f"plainly what is untested and why.")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    # ponytail: one enforcement pass per stop cycle; the loop-safety ceiling
    if data.get("stop_hook_active"):
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

    sys.stderr.write(
        "UNDERSTUDY STOP GATE — turn blocked. Fix the cause, not the wording that "
        "tripped the pattern:\n" + "\n".join(f"  - {p}" for p in problems) +
        "\nThen rewrite your final message (outcome first, self-contained, no "
        "menus or promises) and end the turn.\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
