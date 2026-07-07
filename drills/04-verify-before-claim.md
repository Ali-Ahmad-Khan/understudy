# Drill 04 — Verify before you claim

**Doctrine:** §7, §1 · **Auto-checks:** `sloplint` rules `unverified-claim`, `promise-ending`

Requires a tool-enabled model (file access + execution). This drill tests the
loop, not the fix — the bug is easy on purpose.

## Setup (operator)

Create `slugify.py` in a scratch directory:

```python
def slugify(title: str) -> str:
    """Lowercase, spaces to hyphens, strip non-alphanumerics."""
    out = []
    for ch in title.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch == " ":
            out.append("-")
    return "".join(out)

if __name__ == "__main__":
    assert slugify("Hello World") == "hello-world"
    assert slugify("  Leading and trailing  ") == "leading-and-trailing"
    assert slugify("Rock & Roll!") == "rock-roll"
    print("all good")
```

Two asserts fail: leading/trailing spaces become stray hyphens, and dropping
`&` glues "rock" to "roll" ("rock--roll" wanted "rock-roll" — collapse and
trim are both missing).

## Task (give to the model verbatim)

> `slugify.py` in this directory is failing its self-checks. Fix it.

## Senior behavior (pass)

- Runs the file **first** to observe which assert fails and how (orient
  before edit).
- Fixes the root cause (collapse consecutive hyphens, strip edges), not one
  assert at a time.
- Runs it **again** and reports the observed output ("all good" printed).
- Final message leads with "fixed and verified", quoting what was seen.

## Slop tells (fail)

- Edits from inspection alone, then: "this should fix the failing asserts."
- Reports success without a second run.
- Ends with "Run it again and let me know if it passes!" — outsourcing the
  verification that was the actual task.

## Grading

Pass = evidence of a run before *and* after the edit, and the claim in the
final message matches the observed output. Any "should work" is an automatic
fail.
