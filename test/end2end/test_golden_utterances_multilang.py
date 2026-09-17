"""Multilingual golden-utterance end-to-end coverage for
ovos-skill-pokepedia.

test_golden_utterances.py (superseded by this file) and the per-locale
test_intents_*.py files only exercised en-US/es/fr/it/pt. This skill
registers four Padatious/Padacioso file-intents (get_pokemon_info,
get_pokemon_moves, get_pokemon_type, battle); every locale under locale/
ships real .intent and .voc content for all four. Each golden row is a
literal resolution of that locale's own .intent template lines --
(a|b) alternatives and [a|b]/[x] optional groups resolve to one concrete
choice -- with {pokemon}/{pokemon_a}/{pokemon_b} slots filled from
pikachu/charizard/squirtle, three names every locale's own pokemon.voc
carries verbatim (Pokemon names are not translated across locales). No
translated or invented prose is introduced.

The PokeAPI backend is mocked deterministically (fixtures.fake_get_pokemon)
on the booted skill instance, the same technique test_golden_utterances.py
and _helpers.py used, so the suite stays network-free.

Unlike ovos-skill-alerts' shared-MiniCroft-with-secondary-langs approach
(blocked by ovoscope#179 at multi-locale scale), this suite follows the
ovos-skill-date-time per-locale pattern (test/end2end/test_intents_it_it.py
on that repo's dev branch): one MiniCroft is booted per locale, in turn,
torn down when the module's tests finish. Only the pure-Python, swig-free
padacioso template engine is booted (no padatious training phase, so no
"mycroft.skills.trained" wait across many locales).
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

from .fixtures import fake_get_pokemon

SKILL_ID = "ovos-skill-pokepedia.openvoiceos"

PIPELINE = [
    "ovos-padacioso-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-low",
]

END2END_DIR = Path(__file__).parent

LANGS = [
    "ca-ES", "de-DE", "en-US", "es-ES", "eu-ES", "fr-FR", "gl-ES", "it-IT",
    "kab", "nl-NL", "pt-BR", "pt-PT", "sv-SE",
]

CROSS_LANG_NEGATIVES = [
    ("tell me about the weather", "de-DE", "other-skill (weather) phrasing, german session"),
    ("play some music", "fr-FR", "other-skill (music) phrasing, french session"),
    ("set a timer for 5 minutes", "es-ES", "other-skill (alerts) phrasing, spanish session"),
]


def _candidates(skill_id: str, intent_label: str) -> set:
    base = intent_label[:-len(".intent")] if intent_label.endswith(".intent") else intent_label
    return {f"{skill_id}:{intent_label}", f"{skill_id}:{base}"}


def _load_rows(lang):
    path = END2END_DIR / f"golden_utterances_{lang}.jsonl"
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("needs_manual"):
                continue
            rows.append(row)
    return rows


ALL_ROWS = []
for _lang in LANGS:
    for _row in _load_rows(_lang):
        ALL_ROWS.append(_row)


def _golden_id(row):
    return f"{row['lang']}-{row['intent_label']}-{row['utterance']}"


GOLDEN_ROWS = [pytest.param(r, id=_golden_id(r)) for r in ALL_ROWS]

_MINICROFTS = {}


def _get_minicroft(lang):
    mc = _MINICROFTS.get(lang)
    if mc is None:
        mc = get_minicroft([SKILL_ID], max_wait=150, lang=lang,
                            default_pipeline=PIPELINE)
        loader = mc.plugin_skills[SKILL_ID]
        skill = loader.instance
        client = MagicMock()
        client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
        skill.api_client = client
        _MINICROFTS[lang] = mc
    return mc


@pytest.fixture(scope="module", autouse=True)
def _stop_all_minicrofts():
    yield
    for mc in _MINICROFTS.values():
        mc.stop()
    _MINICROFTS.clear()


def _types(mc, text, lang, session_id):
    session = Session(session_id)
    session.lang = lang
    session.pipeline = list(PIPELINE)
    session.blacklisted_intents = []
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": lang},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(mc, eof_msgs=["mycroft.skill.handler.start"])
    capture.capture(utterance, timeout=30)
    return [m.msg_type for m in capture.finish()]


@pytest.mark.timeout(180)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=_golden_id)
def test_golden_utterance_multilang(row):
    mc = _get_minicroft(row["lang"])
    candidates = _candidates(SKILL_ID, row["intent_label"])
    types = _types(mc, row["utterance"], row["lang"], f"golden-{_golden_id(row)}")
    assert any(t in candidates for t in types), (
        f"[{row['lang']}] {row['utterance']!r}: expected one of {sorted(candidates)!r}, got {types!r}"
    )


@pytest.mark.timeout(180)
@pytest.mark.parametrize("negative", CROSS_LANG_NEGATIVES, ids=lambda n: f"{n[1]}-{n[0]}")
def test_cross_language_negative(negative):
    text, lang, _why = negative
    mc = _get_minicroft(lang)
    types = _types(mc, text, lang, f"negative-{lang}-{text}")
    claimed = any(t.startswith(f"{SKILL_ID}:") for t in types)
    assert not claimed, f"[{lang}] {text!r} was incorrectly claimed by {SKILL_ID}"
