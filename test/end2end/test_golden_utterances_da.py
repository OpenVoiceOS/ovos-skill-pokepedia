"""Golden-utterance end-to-end coverage for da-DK.

The rows come from ``golden_utterances.jsonl``, filtered to the ``da-DK``
language, and cover the four Padatious file intents of the skill.

Every row whose ``machine_generated`` is false drives a phrasing andlo
wrote and confirmed as a native speaker (#41, carried here from 591acf0).
The three rows that carry ``machine_generated: true`` drive the three
phrasings the machine cut added and andlo has not seen, and the .intent
lines they match are commented as unvouched in the locale.

Run:
    uv run pytest test/end2end/test_golden_utterances_da.py -v
"""
from unittest.mock import MagicMock

import pytest
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from ._helpers import (
    SKILL_ID, _ADAPT_PIPELINE, _PADATIOUS_PIPELINE, _SPOKE, _intent_candidates,
    golden_params, load_golden_rows,
)
from .fixtures import fake_get_pokemon

_NEEDS_MANUAL_REASONS = {}

LANG = "da-DK"
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


def _capture(mc, text, session_id, pipeline):
    session = make_session(
        session_id=session_id,
        pipeline=pipeline,
        blacklisted_intents=[],
        blacklisted_skills=[],
        lang=LANG,
    )
    message = make_utterance_message(text, lang=LANG, session=session)
    cap = CaptureSession(minicroft=mc)
    cap.capture(message, timeout=15)
    return [m.msg_type for m in cap.finish()]


@pytest.mark.timeout(60)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=lambda r: r["utterance"])
def test_golden_utterance_da(minicroft, row):
    candidates = _intent_candidates(row["intent_label"])
    pipeline = _PADATIOUS_PIPELINE if row["intent_type"] == "padatious" else _ADAPT_PIPELINE
    types = _capture(minicroft, row["utterance"], f"golden-da-{row['utterance']}", pipeline=pipeline)
    assert any(t in candidates for t in types), (
        f"{row['utterance']!r}: expected one of {sorted(candidates)!r}, got {types!r}"
    )
    assert set(types) & _SPOKE, (
        f"{row['utterance']!r} matched one of {sorted(candidates)!r} but the skill never spoke: {types!r}"
    )
