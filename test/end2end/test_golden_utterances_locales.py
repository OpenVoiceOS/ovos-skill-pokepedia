"""Golden-utterance end-to-end coverage for every other shipped locale.

Each ``golden_utterances_<lang>.jsonl`` file feeds this runner, except en-US
and da-DK, which have their own modules. The runner boots one single-language
MiniCroft per locale and asserts that each row reaches the intent its
``intent_label`` names and that the skill speaks. The PokeAPI backend is the
deterministic fake from ``fixtures.py``.

Run:
    uv run pytest test/end2end/test_golden_utterances_locales.py -v
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from ._helpers import (
    SKILL_ID, _ADAPT_PIPELINE, _PADATIOUS_PIPELINE, _SPOKE, _intent_candidates,
    golden_langs, load_golden_rows,
)
from .fixtures import fake_get_pokemon

LOCALE_ROOT = Path(__file__).parents[2] / "ovos_skill_pokepedia" / "locale"

OWN_MODULES = {"en-US", "da-DK"}
LANGS = [lang for lang in golden_langs() if lang not in OWN_MODULES]
ROWS = [
    pytest.param(lang, row, id=f"{lang}-{row['utterance']}")
    for lang in LANGS
    for row in load_golden_rows(lang)
]


@pytest.fixture(scope="module")
def minicrofts():
    """Hold one MiniCroft at a time; the rows arrive grouped by language."""
    booted = {}

    def get(lang):
        if lang not in booted:
            for mc in booted.values():
                mc.stop()
            booted.clear()
            LOG.set_level("CRITICAL")
            mc = get_minicroft([SKILL_ID], lang=lang)
            client = MagicMock()
            client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
            mc.plugin_skills[SKILL_ID].instance.api_client = client
            booted[lang] = mc
        return booted[lang]

    yield get
    for mc in booted.values():
        mc.stop()


def _capture(mc, lang, text, pipeline):
    session = make_session(
        session_id=f"golden-{lang}-{text}",
        pipeline=pipeline,
        blacklisted_intents=[],
        blacklisted_skills=[],
        lang=lang,
    )
    message = make_utterance_message(text, lang=lang, session=session)
    cap = CaptureSession(minicroft=mc)
    cap.capture(message, timeout=15)
    return [m.msg_type for m in cap.finish()]


@pytest.mark.timeout(600)
@pytest.mark.parametrize("lang,row", ROWS)
def test_golden_utterance_locale(minicrofts, lang, row):
    assert row["lang"] == lang
    candidates = _intent_candidates(row["intent_label"])
    pipeline = _PADATIOUS_PIPELINE if row["intent_type"] == "padatious" else _ADAPT_PIPELINE
    types = _capture(minicrofts(lang), lang, row["utterance"], pipeline)
    assert any(t in candidates for t in types), (
        f"{lang} {row['utterance']!r}: expected one of {sorted(candidates)!r}, got {types!r}"
    )
    assert set(types) & _SPOKE, (
        f"{lang} {row['utterance']!r} matched one of {sorted(candidates)!r} but the skill never spoke: {types!r}"
    )


def test_every_shipping_locale_has_a_golden_file():
    golden = {p.stem.split("_", 2)[2] for p in Path(__file__).parent.glob("golden_utterances_*.jsonl")}
    shipping = {d.name for d in LOCALE_ROOT.iterdir() if d.is_dir() and any(d.rglob("*.intent"))}
    assert golden == shipping, f"golden files {sorted(golden ^ shipping)} differ from shipping locales"
