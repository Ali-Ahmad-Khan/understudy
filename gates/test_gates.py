#!/usr/bin/env python3
"""Self-check for the gates: drives them exactly as Claude Code does — JSON on
stdin, transcript/ledger on disk, exit code out. Run: python3 test_gates.py"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_gate(script: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / script)],
                          input=json.dumps(payload), capture_output=True, text=True)


def transcript(tmp: Path, final_text: str) -> str:
    p = tmp / "transcript.jsonl"
    lines = [
        {"type": "user", "message": {"content": [{"type": "text", "text": "fix the bug"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": final_text}]}},
    ]
    p.write_text("\n".join(json.dumps(l) for l in lines))
    return str(p)


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)

    # 1. Ledger recorder: an edit then an exec land in the session file.
    for payload in (
        {"session_id": "s1", "cwd": td, "tool_name": "Edit",
         "tool_input": {"file_path": "/repo/app.py"}},
        {"session_id": "s1", "cwd": td, "tool_name": "Bash",
         "tool_input": {"command": "pytest -q"}},
    ):
        r = run_gate("gate_edit.py", payload)
        assert r.returncode == 0, r.stderr
    ledger = tmp / ".claude" / "understudy" / "state" / "s1.jsonl"
    events = [json.loads(l) for l in ledger.read_text().splitlines()]
    assert [e["t"] for e in events] == ["edit", "exec"], events

    # 2. Stop gate BLOCKS: code edit, no exec after, completion claim + slop ending.
    run_gate("gate_edit.py", {"session_id": "s2", "cwd": td, "tool_name": "Edit",
                              "tool_input": {"file_path": "/repo/auth.js"}})
    slop_end = ("Great question! I patched the handler and this should fix the "
                "login issue — it's done now.\n\nWould you like me to also add "
                "tests? Let me know which option you prefer!")
    r = run_gate("gate_stop.py", {"session_id": "s2", "cwd": td,
                                  "transcript_path": transcript(tmp, slop_end),
                                  "stop_hook_active": False})
    assert r.returncode == 2, f"expected block, got {r.returncode}: {r.stderr}"
    assert "verification-ledger" in r.stderr and "menu-ending" in r.stderr, r.stderr

    # 3. Stop gate ALLOWS: exec after the edit + clean, evidenced final message.
    run_gate("gate_edit.py", {"session_id": "s2", "cwd": td, "tool_name": "Bash",
                              "tool_input": {"command": "npm test"}})
    clean = ("The login bug is fixed and verified: the null session token crashed "
             "the handler, so I added the guard where all three callers route "
             "through, then re-ran the suite — 42 passed, 0 failed.")
    r = run_gate("gate_stop.py", {"session_id": "s2", "cwd": td,
                                  "transcript_path": transcript(tmp, clean),
                                  "stop_hook_active": False})
    assert r.returncode == 0, f"clean message blocked: {r.stderr}"

    # 4. Loop safety: same slop message passes when stop_hook_active is set.
    r = run_gate("gate_stop.py", {"session_id": "s2", "cwd": td,
                                  "transcript_path": transcript(tmp, slop_end),
                                  "stop_hook_active": True})
    assert r.returncode == 0, "stop_hook_active must disarm the gate"

    # 5. Doc-only edits never trigger the ledger check.
    run_gate("gate_edit.py", {"session_id": "s3", "cwd": td, "tool_name": "Write",
                              "tool_input": {"file_path": "/repo/README.md"}})
    r = run_gate("gate_stop.py", {"session_id": "s3", "cwd": td,
                                  "transcript_path": transcript(tmp, "README rewrite is done."),
                                  "stop_hook_active": False})
    assert r.returncode == 0, f"doc edit wrongly gated: {r.stderr}"

    # 6. Garbage stdin never breaks the session.
    for script in ("gate_edit.py", "gate_stop.py"):
        r = subprocess.run([sys.executable, str(HERE / script)],
                           input="not json{", capture_output=True, text=True)
        assert r.returncode == 0, f"{script} crashed on garbage input"

    # 7. Hard block cap: after 5 blocks in one session, the gate stands down —
    #    loop safety must hold even if the harness never sets stop_hook_active.
    slop_t = transcript(tmp, slop_end)
    for i in range(5):
        r = run_gate("gate_stop.py", {"session_id": "s5", "cwd": td,
                                      "transcript_path": slop_t,
                                      "stop_hook_active": False})
        assert r.returncode == 2, f"block {i + 1} did not fire: {r.stderr}"
    r = run_gate("gate_stop.py", {"session_id": "s5", "cwd": td,
                                  "transcript_path": slop_t,
                                  "stop_hook_active": False})
    assert r.returncode == 0, "block cap not enforced — infinite loop risk"

print("ok — 7 gate scenarios pass (block, allow, loop-safety, doc-exempt, resilience, block-cap)")
