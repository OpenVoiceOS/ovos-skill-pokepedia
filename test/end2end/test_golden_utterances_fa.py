"""Golden-utterance end-to-end coverage for fa-IR.

The rows come from ``golden_utterances.jsonl``, filtered to the ``fa-IR``
language. Each row covers one of the three intent-template lines that
carried a dead mid-template Persian question mark (``؟``, U+061F) before
the fix in OPE-1710. Two of the three lines produced
``ovos.intent.unmatched`` before the fix. The third line matched
``get_pokemon_info`` but captured a corrupted slot value, because the
mark broke the token boundary padatious uses to split the trailing free
slot. Each row asserts the captured ``pokemon`` slot value, not only
routing, so the slot-corruption case cannot pass on a line that still
routes but captures the wrong value.

No native speaker is on record for fa-IR in this repository. Every row
here is machine-generated from the skill's own template lines, not an
original phrasing.

Run:
    uv run pytest test/end2end/test_golden_utterances_fa.py -v
"""
from unittest.mock import MagicMock

import pytest
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from ._helpers import (
    SKILL_ID, _PADATIOUS_PIPELINE, _SPOKE, _intent_candidates,
    golden_params, load_golden_rows,
)
from .fixtures import fake_get_pokemon

_NEEDS_MANUAL_REASONS = {}

LANG = "fa-IR"
GOLDEN_ROWS = golden_params(load_golden_rows(LANG), _NEEDS_MANUAL_REASONS)


@pytest.fixture(scope="module")
def minicroft():
    LOG.set_level("CRITICAL")
    mc = get_minicroft([SKILL_ID], lang=LANG)
    loader = mc.plugin_skills[SKILL_ID]
    skill = loader.instance
    client = MagicMock()
    client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
    skill.api_client = client
    yield mc
    mc.stop()


def _capture(mc, text, session_id):
    session = make_session(
        session_id=session_id,
        pipeline=_PADATIOUS_PIPELINE,
        blacklisted_intents=[],
        blacklisted_skills=[],
        lang=LANG,
    )
    message = make_utterance_message(text, lang=LANG, session=session)
    cap = CaptureSession(minicroft=mc)
    cap.capture(message, timeout=15)
    return cap.finish()


@pytest.mark.timeout(60)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=lambda r: r["utterance"])
def test_golden_utterance_fa(minicroft, row):
    candidates = _intent_candidates(row["intent_label"])
    messages = _capture(minicroft, row["utterance"], f"golden-fa-{row['utterance']}")
    types = [m.msg_type for m in messages]
    assert any(t in candidates for t in types), (
        f"{row['utterance']!r}: expected one of {sorted(candidates)!r}, got {types!r}"
    )
    assert set(types) & _SPOKE, (
        f"{row['utterance']!r} matched one of {sorted(candidates)!r} but the skill never spoke: {types!r}"
    )
    matched = next(m for m in messages if m.msg_type in candidates)
    for slot, expected_value in row.get("expected_slots", {}).items():
        actual_value = (matched.data.get(slot) or "").strip()
        assert actual_value == expected_value, (
            f"{row['utterance']!r}: expected slot {slot!r} to capture "
            f"{expected_value!r}, got {actual_value!r}"
        )
