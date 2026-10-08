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
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
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

GOLDEN_DIR = Path(__file__).parent


def golden_langs() -> list:
    """Return every language that has a ``golden_utterances_<lang>.jsonl`` file."""
    return sorted(p.stem.removeprefix("golden_utterances_")
                  for p in GOLDEN_DIR.glob("golden_utterances_*.jsonl"))


def load_golden_rows(lang: str) -> list:
    """Return the golden rows of one language."""
    path = GOLDEN_DIR / f"golden_utterances_{lang}.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def golden_params(rows: list) -> list:
    """Every row runs as a real assertion.

    ``needs_manual`` marks a row no native speaker has vouched for; it does
    not mark a known failure, so it never turns a row into an xfail.
    """
    return [pytest.param(row, id=row["utterance"]) for row in rows]


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
