#!/usr/bin/env python3
"""sloplint — deterministic linter for AI-agent output.

Grades a model's final message against the Understudy doctrine (§9 anti-slop
table, §10 checklist). Reads a file or stdin, strips fenced code blocks, and
flags generation-shaped anti-patterns. No dependencies, no LLM calls — the
same text always gets the same score, so it can gate CI or A/B a doctrine.

Usage:
    sloplint.py response.md
    some-agent ... | sloplint.py --json -
    sloplint.py --threshold 2 response.md   # stricter gate

Exit codes: 0 clean (score <= threshold), 1 over threshold, 2 usage error.
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

FENCE_RE = re.compile(r"```.*?(```|\Z)", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")

# Each rule: (id, weight, human message). Detection logic lives in lint().
RULES = {
    "preamble-filler":    (2, "opens with filler instead of the outcome"),
    "buried-lede":        (1, "first line is a header, not an outcome sentence"),
    "restates-question":  (1, "opens by restating the question back"),
    "hedge-padding":      (1, "hedging boilerplate ('it's important to note', ...)"),
    "unverified-claim":   (3, "claims success without evidence ('should work', ...)"),
    "menu-ending":        (2, "ends by outsourcing a decision ('would you like...')"),
    "promise-ending":     (2, "ends with a promise instead of done work ('I'll now...')"),
    "arrow-chain":        (1, "arrow-chain shorthand instead of sentences"),
    "structure-overhead": (2, "headers/bullet ceremony on a short answer"),
    "option-sprawl":      (2, "enumerates alternatives instead of deciding"),
    "conclusion-chrome":  (1, "closing boilerplate ('in conclusion', 'hope this helps')"),
    "emoji-confetti":     (1, "decorative emoji"),
}

PREAMBLE_RE = re.compile(
    r"^(great question|good question|excellent question|certainly[,!]|sure[,!]"
    r"|absolutely[,!]|of course[,!]|i'd be happy to|i would be happy to"
    r"|happy to help|what a great|thanks for asking)", re.I)
RESTATE_RE = re.compile(r"\b(you('|’)re asking|you asked|so you want|your question is)", re.I)
HEDGES = (
    "it's important to note", "it is important to note", "it's worth noting",
    "it is worth noting", "keep in mind that", "please note that",
    "as an ai", "as a language model",
)
UNVERIFIED = (
    "should work", "should now work", "should be working", "ought to work",
    "in theory", "this will fix", "that will fix", "should fix",
    "should resolve", "likely works", "probably works",
)
MENU_RE = re.compile(
    r"(would you like|do you want me to|shall i\b|want me to\b"
    r"|let me know (if|which|whether|how|what))", re.I)
PROMISE_RE = re.compile(r"\b(i'll now|i will now|i'll go ahead|next,? i (will|'ll)|next steps?:)", re.I)
ARROW_RE = re.compile(r"(→[^\n]*→|->[^\n]*->)")
OPTIONS = ("alternatively", "another option", "another approach", "you could also", "you might also")
CHROME = ("in conclusion", "i hope this helps", "hope this helps",
          "feel free to", "don't hesitate to", "happy coding")


def _is_emoji(ch: str) -> bool:
    if ch in "✅❌⚠⭐❤✨✔✳❗❕":  # common symbol-block emoji outside the 1F000+ range
        return True
    return ord(ch) >= 0x1F000 and unicodedata.category(ch) == "So"


def lint(text: str) -> list[dict]:
    """Return findings for one message. Prose checks run on code-stripped text."""
    prose = INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))
    lines = [l.strip() for l in prose.splitlines()]
    nonempty = [l for l in lines if l]
    findings = []

    def hit(rule, line_no, excerpt):
        weight, msg = RULES[rule]
        findings.append({"rule": rule, "weight": weight, "line": line_no,
                         "message": msg, "excerpt": excerpt[:90]})

    # --- opening ---
    if nonempty:
        first = nonempty[0]
        first_no = lines.index(first) + 1
        if PREAMBLE_RE.search(first):
            hit("preamble-filler", first_no, first)
        if RESTATE_RE.search(first):
            hit("restates-question", first_no, first)
        if first.startswith("#"):
            hit("buried-lede", first_no, first)

    # --- line-scoped patterns ---
    for i, line in enumerate(lines, 1):
        low = line.lower()
        for h in HEDGES:
            if h in low:
                hit("hedge-padding", i, line)
                break
        for u in UNVERIFIED:
            if u in low:
                hit("unverified-claim", i, line)
                break
        if ARROW_RE.search(line):
            hit("arrow-chain", i, line)
        for c in CHROME:
            if c in low:
                hit("conclusion-chrome", i, line)
                break

    # --- ending (last paragraph of prose) ---
    paras = [p.strip() for p in re.split(r"\n\s*\n", prose) if p.strip()]
    if paras:
        last = paras[-1]
        last_no = len(lines)
        if MENU_RE.search(last):
            hit("menu-ending", last_no, last.splitlines()[-1])
        if PROMISE_RE.search(last):
            hit("promise-ending", last_no, last.splitlines()[-1])

    # --- whole-message shape ---
    words = len(re.findall(r"\w+", prose))
    headers = sum(1 for l in nonempty if l.startswith("#"))
    bullets = sum(1 for l in nonempty if re.match(r"^([-*+]|\d+\.)\s", l))
    if words < 120 and (headers >= 1 or bullets >= 5):
        hit("structure-overhead", 1,
            f"{words} words with {headers} header(s), {bullets} bullet(s)")

    opt_hits = sum(prose.lower().count(o) for o in OPTIONS)
    if opt_hits >= 2:
        hit("option-sprawl", 1, f"{opt_hits} alternative-markers with no verdict required")

    emoji = sum(1 for ch in prose if _is_emoji(ch))
    if emoji > 2:
        hit("emoji-confetti", 1, f"{emoji} emoji")

    return findings


def score(findings: list[dict]) -> int:
    return sum(f["weight"] for f in findings)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sloplint", description=__doc__.splitlines()[0])
    ap.add_argument("path", help="file to lint, or '-' for stdin")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--threshold", type=int, default=3,
                    help="max acceptable score before exit 1 (default 3)")
    args = ap.parse_args(argv)

    try:
        text = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"sloplint: {e}", file=sys.stderr)
        return 2

    findings = lint(text)
    total = score(findings)
    verdict = "clean" if total <= args.threshold else "slop"

    if args.json:
        print(json.dumps({"score": total, "threshold": args.threshold,
                          "verdict": verdict, "findings": findings}, indent=2))
    else:
        for f in sorted(findings, key=lambda f: f["line"]):
            print(f"{f['line']:>4}  {f['rule']:<20} (+{f['weight']})  {f['message']}")
            print(f"      | {f['excerpt']}")
        print(f"\nscore {total} / threshold {args.threshold} — {verdict.upper()}")

    return 0 if total <= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
