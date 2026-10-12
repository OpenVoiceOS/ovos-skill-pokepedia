"""Shared infrastructure for pokepedia intent-routing tests.

The assertions here are deliberately *drift-immune*: instead of pinning an
exact, ordered ``expected_messages`` sequence (which breaks whenever the bus
vocabulary shifts — e.g. the ``speak`` -> ``ovos.utterance.speak`` rename, or an
extra ``ovos.intent.matched`` signal), each test asserts only the two facts it
actually cares about:

1. the ``{skill_id}:<Intent>`` match message fired (correct routing), and
2. a user-visible side effect happened (the skill spoke).

Routing runs on padacioso, which matches the skill's ``.intent`` file
intents. Every session sets ``blacklisted_intents=[]``: some padacioso
versions raise ``TypeError`` on a session whose ``blacklisted_intents`` is
None.
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
_PADACIOSO_PIPELINE = [
    "ovos-padacioso-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-low",
]

# Both spellings of the "the skill spoke" side effect: ovos-core emits the
# legacy ``speak`` and/or the renamed ``ovos.utterance.speak`` depending on
# version. Matching either keeps the assertion immune to that rename.
_SPOKE = {"speak", "ovos.utterance.speak"}

GOLDEN_PATH = Path(__file__).parent / "golden_utterances.jsonl"


def load_golden_rows(lang: str) -> list:
    """Return the golden rows of one language.

    A row without a ``lang`` key belongs to en-US, the reference locale.
    """
    rows = []
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("lang", "en-US") == lang:
                rows.append(row)
    return rows


def golden_params(rows: list, needs_manual_reasons: dict) -> list:
    params = []
    for row in rows:
        if row.get("needs_manual"):
            reason = needs_manual_reasons.get(row["utterance"])
            assert reason, f"missing needs_manual reason for {row['utterance']!r}"
            params.append(pytest.param(row, id=row["utterance"],
                                       marks=pytest.mark.xfail(strict=True, reason=reason)))
        else:
            params.append(pytest.param(row, id=row["utterance"]))
    return params


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
        # single-language minicroft registers the intents in one locale instead of
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

    def _assert_routes(self, utterance: str, intent_name: str, *, padacioso: bool) -> list:
        pipeline = _PADACIOSO_PIPELINE if padacioso else _ADAPT_PIPELINE
        types = self._capture(utterance, pipeline)
        candidates = _intent_candidates(intent_name)
        self.assertTrue(
            any(t in candidates for t in types),
            f"{utterance!r} did not route to one of {sorted(candidates)!r} "
            f"(captured: {types})",
        )
        return types

    def _assert_intent(self, utterance: str, intent_name: str, *, padacioso: bool):
        types = self._assert_routes(utterance, intent_name, padacioso=padacioso)
        candidates = _intent_candidates(intent_name)
        self.assertTrue(
            _SPOKE.intersection(types),
            f"{utterance!r} matched one of {sorted(candidates)!r} but the "
            f"skill never spoke (captured: {types})",
        )

    def _assert_no_intent(self, utterance: str):
        # Mixed Adapt+Padacioso pipeline; nothing should match, so no intent
        # message from this skill.
        pipeline = _PADACIOSO_PIPELINE[:1] + _ADAPT_PIPELINE[:1]
        types = self._capture(utterance, pipeline)
        skill_intents = [t for t in types if t.startswith(f"{SKILL_ID}:")]
        self.assertFalse(
            skill_intents,
            f"{utterance!r} unexpectedly routed to {skill_intents}",
        )
