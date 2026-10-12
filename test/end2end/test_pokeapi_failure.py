"""A PokeAPI outage makes the skill speak an error instead of crashing.

The intent still routes (padacioso), the handler catches
``PokemonPokeAPIError``, and the skill speaks ``error_not_found``.
"""
from unittest.mock import MagicMock

import pytest
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from ovos_skill_pokepedia.api_client import PokemonPokeAPIError

from ._helpers import SKILL_ID, _PADACIOSO_PIPELINE, _SPOKE

LANG = "en-US"


@pytest.fixture(scope="module")
def minicroft():
    LOG.set_level("CRITICAL")
    mc = get_minicroft([SKILL_ID], lang=LANG)
    yield mc
    mc.stop()


@pytest.mark.timeout(60)
def test_pokeapi_failure_is_graceful(minicroft):
    skill = minicroft.plugin_skills[SKILL_ID].instance
    original_client = skill.api_client
    failing_client = MagicMock()
    failing_client.get_pokemon.side_effect = PokemonPokeAPIError("simulated PokeAPI outage")
    skill.api_client = failing_client
    try:
        session = make_session(session_id="graceful-failure", pipeline=_PADACIOSO_PIPELINE,
                               blacklisted_intents=[], blacklisted_skills=[], lang=LANG)
        message = make_utterance_message("tell me about the pokemon pikachu", lang=LANG,
                                         session=session)
        cap = CaptureSession(minicroft=minicroft)
        cap.capture(message, timeout=15)
        messages = cap.finish()
    finally:
        skill.api_client = original_client

    types = [m.msg_type for m in messages]
    assert f"{SKILL_ID}:get_pokemon_info" in types, (
        f"expected the intent to still route despite backend failure, got {types!r}"
    )
    dialogs = [m.data.get("meta", {}).get("dialog") for m in messages if m.msg_type in _SPOKE]
    assert "error_not_found" in dialogs, (
        f"expected the error_not_found dialog, got {dialogs!r}"
    )
