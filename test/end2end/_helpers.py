"""Shared infrastructure for pokepedia intent-routing tests.

The assertions here are deliberately *drift-immune*: instead of pinning an
exact, ordered ``expected_messages`` sequence (which breaks whenever the bus
vocabulary shifts — e.g. the ``speak`` -> ``ovos.utterance.speak`` rename, or an
extra ``ovos.intent.matched`` signal), each test asserts only the two facts it
actually cares about:

1. the ``{skill_id}:<Intent>`` match message fired (correct routing), and
2. a user-visible side effect happened (the skill spoke).

Routing is pinned to Adapt (keyword intents: info / moves / type) and Padatious
(the ``battle.intent`` file intent). Padacioso is deliberately excluded: on
``padacioso==1.1.1a1`` it raises ``TypeError: NoneType is not iterable`` on any
session with ``blacklisted_intents=None``, which aborts the whole pipeline
before any stage can match. Every session also forces ``blacklisted_intents=[]``
as belt-and-braces against that crash.
"""
from unittest.mock import MagicMock

from ovos_bus_client.session import Session
from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from .fixtures import fake_get_evolution_chain, fake_get_pokemon

SKILL_ID = "ovos-skill-pokepedia.openvoiceos"

_ADAPT_PIPELINE = [
    "ovos-adapt-pipeline-plugin-high",
    "ovos-adapt-pipeline-plugin-medium",
    "ovos-adapt-pipeline-plugin-low",
]
_PADATIOUS_PIPELINE = [
    "ovos-padatious-pipeline-plugin-high",
    "ovos-padatious-pipeline-plugin-medium",
    "ovos-padatious-pipeline-plugin-low",
]

# Both spellings of the "the skill spoke" side effect: ovos-core emits the
# legacy ``speak`` and/or the renamed ``ovos.utterance.speak`` depending on
# version. Matching either keeps the assertion immune to that rename.
_SPOKE = {"speak", "ovos.utterance.speak"}


def _intent_candidates(intent_name: str) -> set:
    """Different padatious/padacioso plugin versions register the
    matched-intent bus event under different normalizations of the
    ``.intent`` filename basename -- observed variants include the bare
    basename with no extension (current OVOS-INTENT-2 naming, eg.
    ``battle`` for ``battle.intent``, see ovos-skill-parrot#119) and the
    basename with the extension kept. Candidates cover both so tests aren't
    pinned to whichever naming happens to be installed (same pattern as
    ovos-skill-volume/ovos-skill-ggwave's golden suites)."""
    base = intent_name[:-len(".intent")] if intent_name.endswith(".intent") else intent_name
    return {f"{SKILL_ID}:{intent_name}", f"{SKILL_ID}:{base}"}


def _session_after(messages, session):
    """Return the session as it stands AFTER a turn.

    A named session keeps no state in ``SessionManager`` (OVOS-SESSION-2
    §2.2): it travels by value in ``message.context``. A skill that writes
    intent context writes it on its own copy, and that copy reaches the
    caller only on the messages the skill derives after the write. So a
    second turn that shares nothing but the session ID starts from an empty
    context, whatever the skill did, and a test built that way can never show
    a context fallback working.

    A multi-turn test therefore takes the newest serialized session of this
    conversation out of the capture and drives the next turn from it, the way
    a real client folds the session back from the reply it hears.
    """
    for message in reversed(messages):
        serialized = (message.context or {}).get("session")
        if serialized and serialized.get("session_id") == session.session_id:
            return Session.deserialize(serialized)
    return session


def _spoken(messages):
    """Every utterance actually spoken in this capture."""
    return [m.data.get("utterance", "") for m in messages
            if m.msg_type in _SPOKE]


class IntentRoutingMixin:
    """Mixin used by per-locale TestCases to assert intent routing.

    Subclasses must define class attribute ``LANG`` (e.g. ``"en-US"``).
    """

    LANG: str = "en-US"

    @classmethod
    def setUpClass(cls):
        LOG.set_level("DEBUG")
        # Boot in this subclass's language only (no secondary_langs): a
        # single-language minicroft trains Padatious in one locale instead of
        # five, so each per-locale module stays fast and the whole matrix stays
        # well under the CI job timeout.
        cls.minicroft = get_minicroft([SKILL_ID], lang=cls.LANG)
        loader = cls.minicroft.plugin_skills[SKILL_ID]
        skill = loader.instance
        client = MagicMock()
        client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
        client.get_evolution_chain.side_effect = lambda name: fake_get_evolution_chain(name)
        skill.api_client = client

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _new_session(self, pipeline, session_id: str):
        return make_session(
            session_id=session_id,
            pipeline=pipeline,
            blacklisted_intents=[],
            blacklisted_skills=[],
            lang=self.LANG,
        )

    def _capture_messages(self, utterance: str, pipeline, *, session_id: str = None,
                           session=None):
        # A caller passing a `session` OBJECT drives a multi-turn
        # conversation: see `_session_after` for why the object, and not the
        # id, is what carries state. A caller passing only a `session_id`
        # gets one fresh session, same as a caller passing neither.
        if session is None:
            session_id = session_id or f"pokepedia-{self.LANG}-{abs(hash(utterance))}"
            session = self._new_session(pipeline, session_id)
        message = make_utterance_message(utterance, lang=self.LANG, session=session)
        cap = CaptureSession(minicroft=self.minicroft)
        cap.capture(message, timeout=15)
        return cap.finish()

    def _capture(self, utterance: str, pipeline, *, session_id: str = None):
        return [m.msg_type for m in
                self._capture_messages(utterance, pipeline, session_id=session_id)]

    def _spoken_texts(self, utterance: str, pipeline, *, session_id: str = None):
        """Return every utterance actually spoken (``speak``/``ovos.utterance.speak``
        payload text) for this capture, so a test can tell WHICH answer was
        given, not just that some speak event fired."""
        messages = self._capture_messages(utterance, pipeline, session_id=session_id)
        return _spoken(messages)

    def _assert_routes(self, utterance: str, intent_name: str, *, padatious: bool,
                        session_id: str = None) -> list:
        pipeline = _PADATIOUS_PIPELINE if padatious else _ADAPT_PIPELINE
        types = self._capture(utterance, pipeline, session_id=session_id)
        candidates = _intent_candidates(intent_name)
        self.assertTrue(
            any(t in candidates for t in types),
            f"{utterance!r} did not route to one of {sorted(candidates)!r} "
            f"(captured: {types})",
        )
        return types

    def _assert_intent(self, utterance: str, intent_name: str, *, padatious: bool,
                        session_id: str = None):
        types = self._assert_routes(utterance, intent_name, padatious=padatious,
                                     session_id=session_id)
        candidates = _intent_candidates(intent_name)
        self.assertTrue(
            _SPOKE.intersection(types),
            f"{utterance!r} matched one of {sorted(candidates)!r} but the "
            f"skill never spoke (captured: {types})",
        )

    def _assert_no_intent(self, utterance: str):
        # Mixed Adapt+Padatious pipeline; nothing should match, so no intent
        # message from this skill.
        pipeline = _PADATIOUS_PIPELINE[:1] + _ADAPT_PIPELINE[:1]
        types = self._capture(utterance, pipeline)
        skill_intents = [t for t in types if t.startswith(f"{SKILL_ID}:")]
        self.assertFalse(
            skill_intents,
            f"{utterance!r} unexpectedly routed to {skill_intents}",
        )
