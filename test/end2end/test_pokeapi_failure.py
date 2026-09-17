"""If the PokeAPI backend raises, the skill must speak "error.not.found"
gracefully rather than crash the handler or leave the utterance unhandled.

Split out of the former test_golden_utterances.py (en-US only), which is
now test_golden_utterances_multilang.py -- this check is not locale golden
coverage, it is a single backend-failure regression test and stays en-US.
"""
from unittest.mock import MagicMock

import pytest
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from ovos_skill_pokepedia.api_client import PokemonPokeAPIError

from ._helpers import SKILL_ID, _PADATIOUS_PIPELINE, _SPOKE
from .fixtures import fake_get_pokemon

LANG = "en-US"


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


@pytest.mark.timeout(30)
def test_pokeapi_failure_is_graceful(minicroft):
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

    assert f"{SKILL_ID}:get_pokemon_info" in types, (
        f"expected the intent to still route despite backend failure, got {types!r}"
    )
    assert set(types) & _SPOKE, (
        f"expected a graceful spoken fallback response, got {types!r}"
    )
