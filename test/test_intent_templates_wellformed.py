"""A group with one branch is not an optional word.

`hvilke(n) (type|typer)` reads as a choice between `hvilke` and `hvilken`
followed by a choice of nouns, and it is neither: a group with a single branch
degenerates to that branch, so the line only ever produces `hvilken typer` and
the plural it was written for is unreachable. The mistake is invisible in the
file and invisible in a parity check, because the file exists and parses.

Optional words are written `[like this]`.
"""
import re
from pathlib import Path

LOCALES = Path(__file__).resolve().parents[1] / "ovos_skill_pokepedia" / "locale"

SINGLE_BRANCH = re.compile(r"\((?P<branch>[^()|]*)\)")


def test_no_intent_line_carries_a_single_branch_group():
    degenerate = []
    for intent in sorted(LOCALES.glob("*/intents/*.intent")):
        for number, line in enumerate(intent.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            for match in SINGLE_BRANCH.finditer(line):
                degenerate.append(
                    f"{intent.relative_to(LOCALES)}:{number}: "
                    f"({match.group('branch')}) has one branch; "
                    f"write [{match.group('branch')}] to make it optional")
    assert not degenerate, "\n  " + "\n  ".join(degenerate)
