#!/usr/bin/env python3
"""Self-check for sloplint. Run: python3 test_sloplint.py — silence means pass."""

from sloplint import lint, score

SLOP = """\
Great question! You're asking how to fix the login bug.

# Overview

It's important to note that there are several approaches here.

- Option A: patch the handler
- Option B: rewrite the middleware
- Option C: add a retry

Alternatively, you could also use a proxy. Another option is caching.

I updated the handler → redeployed → this should fix the login issue \U0001F680\U0001F389✨

Would you like me to proceed with Option A? Let me know which you prefer!
"""

CLEAN = """\
The login bug is fixed and verified: the null session token was crashing the
handler, so I added the guard in `auth/session.py` where all three callers
route through, then re-ran the auth suite — 42 passed, 0 failed — and
confirmed a real login round-trip against the dev server.

One caveat worth knowing: sessions created during the outage window are
invalid and those users must log in again.
"""

slop_findings = lint(SLOP)
slop_rules = {f["rule"] for f in slop_findings}
clean_findings = lint(CLEAN)

# The slop sample trips every category it stages.
for expected in ("preamble-filler", "restates-question", "hedge-padding",
                 "unverified-claim", "menu-ending", "arrow-chain",
                 "option-sprawl", "emoji-confetti", "structure-overhead"):
    assert expected in slop_rules, f"missing rule: {expected} (got {sorted(slop_rules)})"

assert score(slop_findings) > 3, f"slop sample scored too low: {score(slop_findings)}"
assert score(clean_findings) <= 3, f"clean sample flagged: {clean_findings}"

# Code blocks are exempt from prose rules.
code_only = "Done and verified.\n\n```py\n# should work in theory -> -> ok\n```\n"
assert score(lint(code_only)) == 0, f"code block leaked into prose checks: {lint(code_only)}"

print(f"ok — slop scored {score(slop_findings)}, clean scored {score(clean_findings)}")
