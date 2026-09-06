"""Content-assertion coverage for the speak_dialog names used by the skill.

ovos-workshop falls back to speaking the dialog *name* (dots turned to
spaces) when no matching ``.dialog`` file is found, so a routing test that
only checks "some speak message fired" (as ``test_intents_en.py`` etc. do)
cannot catch a mismatched dialog name -- the fallback still counts as "the
skill spoke". These tests instead capture the actual ``utterance`` text on
the bus and assert it is real, rendered content and never a bare dialog
name such as "battle result" or "error not found".

Run:
    uv run pytest test/end2end/test_spoken_content.py -v
"""
from unittest.mock import MagicMock

import pytest
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from ovos_skill_pokepedia.api_client import PokemonPokeAPIError

from ._helpers import SKILL_ID, _PADATIOUS_PIPELINE
from .fixtures import fake_get_pokemon

LANG = "en-US"

# The literal dialog-NAME fallback strings ovos-workshop speaks when a
# .dialog file is missing -- the exact bug this suite guards against.
_DIALOG_NAME_FALLBACKS = {
    "battle result",
    "pokemon info",
    "pokemon moves",
    "error not found",
    "error no pokemon",
}


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


def _spoken_utterances(mc, text, session_id, pipeline):
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
    messages = cap.finish()
    return [
        m.data["utterance"]
        for m in messages
        if m.msg_type in ("speak", "ovos.utterance.speak") and "utterance" in m.data
    ]


def _assert_real_content(spoken, must_contain):
    assert spoken, f"skill never spoke, expected content containing {must_contain!r}"
    joined = " ".join(spoken).lower()
    for fallback in _DIALOG_NAME_FALLBACKS:
        assert fallback not in joined, (
            f"skill spoke the dialog NAME {fallback!r} instead of rendered "
            f"content: {spoken!r}"
        )
    for needle in must_contain:
        assert needle.lower() in joined, f"expected {needle!r} in spoken text {spoken!r}"


@pytest.mark.timeout(60)
def test_battle_speaks_rendered_result(minicroft):
    spoken = _spoken_utterances(
        minicroft, "who wins charmander or pikachu", "battle-content",
        pipeline=_PADATIOUS_PIPELINE,
    )
    _assert_real_content(spoken, ["charmander", "pikachu", "winner"])


@pytest.mark.timeout(60)
def test_info_speaks_rendered_content(minicroft):
    spoken = _spoken_utterances(
        minicroft, "tell me about the pokemon pikachu", "info-content",
        pipeline=_PADATIOUS_PIPELINE,
    )
    _assert_real_content(spoken, ["pikachu", "pokedex"])


@pytest.mark.timeout(60)
def test_moves_speaks_rendered_content(minicroft):
    spoken = _spoken_utterances(
        minicroft, "what moves does pikachu have", "moves-content",
        pipeline=_PADATIOUS_PIPELINE,
    )
    _assert_real_content(spoken, ["pikachu", "moves"])


@pytest.mark.timeout(30)
def test_no_pokemon_named_speaks_real_prompt(minicroft):
    """GetPokemonInfo.intent matching with no {pokemon} slot bound must
    speak the actual "tell me which pokemon" prompt, not "error no pokemon"."""
    loader = minicroft.plugin_skills[SKILL_ID]
    skill = loader.instance
    message_data = {"utterance": "tell me about a pokemon"}
    result = {}

    def _capture_speak(dialog, data=None):
        result["dialog"] = dialog
        result["data"] = data

    original_speak = skill.speak_dialog
    skill.speak_dialog = _capture_speak
    try:
        from ovos_bus_client.message import Message
        skill.handle_get_pokemon_info(Message("intent", {}))
    finally:
        skill.speak_dialog = original_speak

    assert result["dialog"] == "error_no_pokemon"
    text = skill.resources.render_dialog(result["dialog"], result.get("data"))
    assert text.strip() != "error no pokemon"
    assert "pokemon" in text.lower()


@pytest.mark.timeout(30)
def test_backend_failure_speaks_real_not_found_message(minicroft):
    loader = minicroft.plugin_skills[SKILL_ID]
    skill = loader.instance
    original_client = skill.api_client
    failing_client = MagicMock()
    failing_client.get_pokemon.side_effect = PokemonPokeAPIError("simulated outage")
    skill.api_client = failing_client
    try:
        spoken = _spoken_utterances(
            minicroft, "tell me about the pokemon pikachu", "not-found-content",
            pipeline=_PADATIOUS_PIPELINE,
        )
    finally:
        skill.api_client = original_client

    _assert_real_content(spoken, ["pokemon"])
