"""Golden-utterance end-to-end coverage for ovos-skill-pokepedia (en-US).

The master ovoscope corpus carries no rows for
``ovos-skill-pokepedia.openvoiceos``, so ``golden_utterances.jsonl`` is
derived from this skill's own vocab (``tell_me``/``pokemon``/``moves``/
``type``) covering all three Padatious file intents
(``GetPokemonInfo``, ``GetPokemonType``, ``GetPokemonMoves`` -- the last of
which had no e2e coverage at all before this suite, existing
``test_intents_*.py`` files only covered info/type/battle).

See also the entity-registration ordering fix in
``ovos_skill_pokepedia/__init__.py``'s ``initialize()``, which fixed a real,
separate defect (``battle.intent``'s ``{pokemon_a}``/``{pokemon_b}``
entities were never trained at all).

Follows the existing ``test/end2end/_helpers.py`` infrastructure: the
PokeAPI backend is mocked deterministically (``fixtures.fake_get_pokemon``)
for every routing assertion, and one graceful-failure test drives the real
``PokemonPokeAPIError`` path to confirm the skill degrades to
``error.not.found`` rather than crashing.

Run:
    uv run pytest test/end2end/test_golden_utterances.py -v
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from ovos_skill_pokepedia.api_client import PokemonPokeAPIError

from ._helpers import SKILL_ID, _ADAPT_PIPELINE, _PADATIOUS_PIPELINE, _SPOKE, _intent_candidates
from .fixtures import fake_get_evolution_chain, fake_get_pokemon

# Per-row reason for rows marked needs_manual: true in golden_utterances.jsonl.
# The standard requires every row to run (as a real assertion, strict-xfailed
# with a reason if it's a known gap) rather than being silently skipped.
_NEEDS_MANUAL_REASONS = {}

LANG = "en-US"
GOLDEN_PATH = Path(__file__).parent / "golden_utterances.jsonl"

# Confusables from other skills' domains, picked for lexical overlap with
# "tell me about"/"type of"/"moves" phrasing.
NEGATIVE_UTTERANCES = [
    ("tell me about the weather", "ovos-skill-weather.openvoiceos"),
    ("tell me about yourself", "ovos-skill-personal.openvoiceos"),
    ("what type of music is this", "ovos-skill-music.openvoiceos"),
    ("who is confucius", "ovos-skill-confucius-quotes.openvoiceos"),
    ("play some music", "ovos-skill-music.openvoiceos"),
    ("search the web for cats", "ovos-skill-ddg.openvoiceos"),
    ("set a timer for 5 minutes", "ovos-skill-alerts.openvoiceos"),
]


def _load_golden_rows():
    rows = []
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _as_param(row):
    if row.get("needs_manual"):
        reason = _NEEDS_MANUAL_REASONS.get(row["utterance"])
        assert reason, f"missing _NEEDS_MANUAL_REASONS entry for {row['utterance']!r}"
        return pytest.param(row, id=row["utterance"], marks=pytest.mark.xfail(strict=True, reason=reason))
    return pytest.param(row, id=row["utterance"])


GOLDEN_ROWS = [_as_param(r) for r in _load_golden_rows()]


@pytest.fixture(scope="module")
def minicroft():
    LOG.set_level("CRITICAL")
    mc = get_minicroft([SKILL_ID], lang=LANG)
    loader = mc.plugin_skills[SKILL_ID]
    skill = loader.instance
    client = MagicMock()
    client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
    client.get_evolution_chain.side_effect = lambda name: fake_get_evolution_chain(name)
    skill.api_client = client
    yield mc
    mc.stop()


def _capture(mc, text, session_id, pipeline=_ADAPT_PIPELINE):
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


@pytest.mark.timeout(300)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=lambda r: r["utterance"])
def test_golden_utterance(minicroft, row):
    candidates = _intent_candidates(row["intent_label"])
    pipeline = _PADATIOUS_PIPELINE if row["intent_type"] == "padatious" else _ADAPT_PIPELINE
    types = _capture(minicroft, row["utterance"], f"golden-{row['utterance']}", pipeline=pipeline)
    assert any(t in candidates for t in types), (
        f"{row['utterance']!r}: expected one of {sorted(candidates)!r}, got {types!r}"
    )
    assert set(types) & _SPOKE, (
        f"{row['utterance']!r} matched one of {sorted(candidates)!r} but the skill never spoke: {types!r}"
    )


@pytest.mark.timeout(300)
@pytest.mark.parametrize("negative", NEGATIVE_UTTERANCES, ids=lambda n: n[0])
def test_negative_confusable_not_claimed(minicroft, negative):
    text, source_skill = negative
    # single-tier: highest-confidence Adapt only, per this repo's own
    # _assert_no_intent convention.
    types = _capture(minicroft, text, f"negative-{text}", pipeline=_ADAPT_PIPELINE[:1])
    skill_intents = [t for t in types if t.startswith(f"{SKILL_ID}:")]
    assert not skill_intents, (
        f"{text!r} (from {source_skill}) was incorrectly claimed by {SKILL_ID}: {skill_intents!r}"
    )


@pytest.mark.timeout(300)
def test_pokeapi_failure_is_graceful(minicroft):
    """If the PokeAPI backend raises, the skill must speak "error.not.found"
    gracefully rather than crash the handler or leave the utterance
    unhandled."""
    loader = minicroft.plugin_skills[SKILL_ID]
    skill = loader.instance
    original_client = skill.api_client
    failing_client = MagicMock()
    failing_client.get_pokemon.side_effect = PokemonPokeAPIError("simulated PokeAPI outage")
    skill.api_client = failing_client
    try:
        types = _capture(
            minicroft, "tell me about the pokemon pikachu", "graceful-failure",
            pipeline=_PADATIOUS_PIPELINE,
        )
    finally:
        skill.api_client = original_client

    assert f"{SKILL_ID}:GetPokemonInfo" in types, (
        f"expected the intent to still route despite backend failure, got {types!r}"
    )
    assert set(types) & _SPOKE, (
        f"expected a graceful spoken fallback response, got {types!r}"
    )
