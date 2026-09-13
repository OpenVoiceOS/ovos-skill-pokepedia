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
from time import monotonic, sleep
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
        cls._await_padatious_training()
        loader = cls.minicroft.plugin_skills[SKILL_ID]
        skill = loader.instance
        client = MagicMock()
        client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
        skill.api_client = client

    @classmethod
    def _await_padatious_training(cls, timeout: float = 120.0):
        """Block until Padatious has compiled this locale's container.

        Padatious trains on a background thread and answers nothing until
        the container is compiled. ovoscope only waits for that when it
        saw the registration messages go by, and it can miss them, in
        which case it returns while training is still running and every
        Padatious assertion fails as an unmatched utterance. Waiting on
        the engine's own state instead of on a bus signal is immune to
        that: `finished_training_event` is clear while a training pass
        runs and `needs_compile` stays true until the container can match.
        """
        plugin = cls.minicroft.intents.pipeline_plugins.get(
            "ovos-padatious-pipeline-plugin")
        trained = getattr(plugin, "finished_training_event", None)
        if trained is None:  # Padatious absent from this pipeline
            return
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            container = plugin.containers.get(cls.LANG)
            if trained.is_set() and container is not None and not container.needs_compile:
                return
            sleep(0.25)
        raise RuntimeError(
            f"Padatious did not finish training {cls.LANG} within {timeout}s; "
            "every Padatious assertion below would fail as an unmatched "
            "utterance, which would read as a routing defect"
        )

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

    def _assert_routes(self, utterance: str, intent_name: str, *, padatious: bool) -> list:
        pipeline = _PADATIOUS_PIPELINE if padatious else _ADAPT_PIPELINE
        types = self._capture(utterance, pipeline)
        candidates = _intent_candidates(intent_name)
        self.assertTrue(
            any(t in candidates for t in types),
            f"{utterance!r} did not route to one of {sorted(candidates)!r} "
            f"(captured: {types})",
        )
        return types

    def _assert_intent(self, utterance: str, intent_name: str, *, padatious: bool):
        types = self._assert_routes(utterance, intent_name, padatious=padatious)
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
