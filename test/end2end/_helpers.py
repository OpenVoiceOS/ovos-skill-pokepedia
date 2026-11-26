"""Shared infrastructure for pokepedia intent-routing tests.

The assertions are drift-immune: instead of pinning an exact, ordered
``expected_messages`` sequence, each test asserts only the two facts it cares
about:

1. the request reached the expected ``{skill_id}:<intent>`` topic;
2. a user-visible side effect happened (the skill spoke).
"""
from unittest.mock import MagicMock

from ovos_bus_client.session import Session
from ovos_utils.log import LOG
from ovoscope import CaptureSession, make_session, make_utterance_message
from ovoscope.routing import PIPELINE, TALLY, get_prototype_minicroft

from .fixtures import fake_get_evolution_chain, fake_get_pokemon

SKILL_ID = "ovos-skill-pokepedia.openvoiceos"
SKILL_INTENTS = [f"{SKILL_ID}:{name}" for name in
                 ("get_pokemon_info", "get_pokemon_moves", "get_pokemon_type",
                  "get_pokemon_evolution", "battle")]

# Both spellings of the "the skill spoke" side effect: ovos-core emits the
# legacy ``speak`` and/or the renamed ``ovos.utterance.speak`` depending on
# version. Matching either keeps the assertion immune to that rename.
_SPOKE = {"speak", "ovos.utterance.speak"}


def intent_topic(intent_name: str) -> str:
    """The bus topic of ``intent_name``, a ``.intent`` file name with or
    without its extension."""
    return f"{SKILL_ID}:{intent_name.removesuffix('.intent')}"


def boot_minicroft(lang: str):
    """A MiniCroft with the skill loaded and the PokeAPI client replaced by
    the fixtures."""
    minicroft = get_prototype_minicroft([SKILL_ID], lang=lang)
    client = MagicMock()
    client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
    client.get_evolution_chain.side_effect = lambda name: fake_get_evolution_chain(name)
    minicroft.plugin_skills[SKILL_ID].instance.api_client = client
    return minicroft


def new_session(lang: str, session_id: str) -> Session:
    """A session that routes through ``PIPELINE``."""
    return make_session(
        session_id=session_id,
        pipeline=PIPELINE,
        blacklisted_intents=[],
        blacklisted_skills=[],
        lang=lang,
    )


def capture(minicroft, utterance: str, lang: str, session_id: str,
            session: Session = None) -> list:
    """The messages ``utterance`` puts on the bus, routed through ``PIPELINE``.

    Pass ``session`` to carry one conversation across turns."""
    session = session or new_session(lang, session_id)
    message = make_utterance_message(utterance, lang=lang, session=session)
    cap = CaptureSession(minicroft=minicroft)
    cap.capture(message, timeout=15)
    return cap.finish()


def session_after(messages, session: Session) -> Session:
    """The session as the skill handed it back on its newest message.

    A named session keeps no state in ``SessionManager``: it travels by value
    in ``message.context``. A second turn that shares only the session id
    starts from an empty context, so a multi-turn test drives the next turn
    from this session, the way a client folds it back from the reply.
    """
    for message in reversed(messages):
        serialized = (message.context or {}).get("session")
        if serialized and serialized.get("session_id") == session.session_id:
            return Session.deserialize(serialized)
    return session


def spoken(messages) -> list:
    """Every utterance the skill spoke in this capture."""
    return [m.data.get("utterance", "") for m in messages if m.msg_type in _SPOKE]


class IntentRoutingMixin:
    """Mixin used by per-locale TestCases to assert intent routing.

    Subclasses must define class attribute ``LANG`` (e.g. ``"en-US"``).
    """

    LANG: str = "en-US"

    @classmethod
    def setUpClass(cls):
        LOG.set_level("DEBUG")
        cls.minicroft = boot_minicroft(cls.LANG)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _messages(self, utterance: str) -> list:
        return capture(self.minicroft, utterance, self.LANG,
                       f"pokepedia-{self.LANG}-{abs(hash(utterance))}")

    def _capture(self, utterance: str) -> list:
        return [m.msg_type for m in self._messages(utterance)]

    def _assert_routes(self, utterance: str, intent_name: str) -> list:
        types = self._capture(utterance)
        TALLY.assert_routed(utterance, intent_topic(intent_name), types)
        return types

    def _assert_intent(self, utterance: str, intent_name: str):
        types = self._assert_routes(utterance, intent_name)
        self.assertTrue(
            _SPOKE.intersection(types),
            f"{utterance!r} matched {intent_topic(intent_name)!r} but the "
            f"skill never spoke (captured: {types})",
        )

    def _assert_no_intent(self, utterance: str):
        TALLY.assert_not_routed(utterance, SKILL_INTENTS, self._capture(utterance))
