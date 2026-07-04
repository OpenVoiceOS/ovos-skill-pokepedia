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

from ovos_utils.log import LOG
from ovoscope import CaptureSession, get_minicroft, make_session, make_utterance_message

from .fixtures import fake_get_pokemon

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


class IntentRoutingMixin:
    """Mixin used by per-locale TestCases to assert intent routing.

    Subclasses must define class attribute ``LANG`` (e.g. ``"en-US"``).
    """

    LANG: str = "en-US"

    @classmethod
    def setUpClass(cls):
        LOG.set_level("DEBUG")
        # No secondary_langs: a single-language minicroft boots in a fraction of
        # the time it takes to train Padatious in five languages, keeping the
        # whole e2e suite well under the CI job timeout.
        cls.minicroft = get_minicroft([SKILL_ID])
        loader = cls.minicroft.plugin_skills[SKILL_ID]
        skill = loader.instance
        client = MagicMock()
        client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
        skill.api_client = client

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _capture(self, utterance: str, pipeline):
        session = make_session(
            session_id=f"pokepedia-{self.LANG}-{abs(hash(utterance))}",
            pipeline=pipeline,
            blacklisted_intents=[],
            blacklisted_skills=[],
            lang=self.LANG,
        )
        message = make_utterance_message(utterance, lang=self.LANG, session=session)
        cap = CaptureSession(minicroft=self.minicroft)
        cap.capture(message, timeout=15)
        return [m.msg_type for m in cap.finish()]

    def _assert_intent(self, utterance: str, intent_name: str, *, padatious: bool):
        pipeline = _PADATIOUS_PIPELINE if padatious else _ADAPT_PIPELINE
        types = self._capture(utterance, pipeline)
        intent_type = f"{SKILL_ID}:{intent_name}"
        self.assertIn(
            intent_type, types,
            f"{utterance!r} did not route to {intent_type} (captured: {types})",
        )
        self.assertTrue(
            _SPOKE.intersection(types),
            f"{utterance!r} matched {intent_type} but the skill never spoke "
            f"(captured: {types})",
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
