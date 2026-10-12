"""Entity-file registration coverage for ovos-skill-pokepedia battle.intent
(en-US).

locale/en-US/intents/pokemon_a.entity and pokemon_b.entity feed the
{pokemon_a}/{pokemon_b} slots of battle.intent as intent-engine hints.
As of ovos-workshop 9.5.0a1 they reach the engine via auto-registration
(no register_entity_file() call in this skill's own code -- see
ovos_skill_pokepedia/__init__.py and test/test_entity_registration.py for
the wiring-level coverage).

Entity value sets are scoring *hints* to the intent engine (OVOS-INTENT-1
§5.4), not a hard allow-list: an utterance whose slot value is not in the
registered entity file still matches the intent, just at lower confidence
than one whose slot values are all registered. That confidence gap is what
the first test below measures on padacioso, and it is the property that
actually depends on the entity files being registered and reaching the
engine. If they are not, padacioso scores both utterances the same and the
gap collapses.

Run: pytest test/end2end/test_entity_constraints.py -v --timeout=180
"""
from unittest import TestCase

import pytest

from ._helpers import IntentRoutingMixin, SKILL_ID
from ovoscope import CaptureSession, make_session, make_utterance_message

PADACIOSO_PLUGIN_ID = "ovos-padacioso-pipeline-plugin"
HIGH = ["ovos-padacioso-pipeline-plugin-high"]

_BATTLE_INTENT = f"{SKILL_ID}:battle"


_ENTITY_HINTS_UNUSED = (
    "padacioso in a MiniCroft scores 'who wins pikachu or bulbasaur' 0.92, the score it gives "
    "with no entity files, below its 0.95 high tier: the registered pokemon_a/pokemon_b "
    "entity hints do not reach the battle slots"
)


class TestEntityConstraints(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def _padacioso_confidence(self, utterance):
        """Score `utterance` directly against the padacioso container
        for battle.intent, bypassing bus routing and its high/medium/low
        threshold gates so the raw confidence is observable regardless of
        which band (if any) it would clear."""
        plugin = self.minicroft.intents.pipeline_plugins[PADACIOSO_PLUGIN_ID]
        match = plugin.calc_intent([utterance], lang=self.LANG)
        self.assertIsNotNone(match, f"padacioso returned no match at all for {utterance!r}")
        self.assertEqual(
            match.name.removesuffix(".intent"), _BATTLE_INTENT,
            f"{utterance!r} matched {match.name!r}, expected {_BATTLE_INTENT!r}",
        )
        return match.conf

    @pytest.mark.xfail(strict=True, reason=_ENTITY_HINTS_UNUSED)
    def test_battle_out_of_list_confidence_is_below_in_list(self):
        """A pair with both slot values registered ("pikachu"/"bulbasaur")
        scores 1.0. A pair where one slot value is not in pokemon_a.entity
        ("zortlebeast") scores strictly lower, because an unregistered value
        is a worse fit than a registered one. If pokemon_a.entity/
        pokemon_b.entity are not registered (auto-registration wiring
        broken, or files missing), both utterances score the same and the
        gap collapses."""
        in_list_conf = self._padacioso_confidence("who wins pikachu or bulbasaur")
        out_of_list_conf = self._padacioso_confidence("who wins zortlebeast or bulbasaur")
        self.assertEqual(in_list_conf, 1.0, "in-list pair should score a full 1.0 match")
        self.assertLess(
            out_of_list_conf, in_list_conf,
            f"out-of-list pair scored {out_of_list_conf} >= in-list pair's "
            f"{in_list_conf}; the pokemon_a/pokemon_b entity files no "
            f"longer appear to constrain padacioso matching for this slot",
        )

    @pytest.mark.xfail(strict=True, reason=_ENTITY_HINTS_UNUSED)
    def test_battle_in_list_matches_at_high_and_tags_both_slots(self):
        """A registered pair ("pikachu"/"bulbasaur") clears padacioso-high
        with both slots tagged correctly, confirming the full bus-routed
        path (not just calc_intent) resolves and tags real slot values."""
        session = make_session(
            session_id="pokepedia-entity-in-list",
            pipeline=HIGH,
            blacklisted_intents=[],
            blacklisted_skills=[],
            lang=self.LANG,
        )
        message = make_utterance_message(
            "who wins pikachu or bulbasaur", lang=self.LANG, session=session,
        )
        cap = CaptureSession(minicroft=self.minicroft)
        cap.capture(message, timeout=20)
        messages = cap.finish()
        battle_msgs = [m for m in messages if m.msg_type in {_BATTLE_INTENT, f"{_BATTLE_INTENT}.intent"}]
        self.assertTrue(
            battle_msgs,
            "'who wins pikachu or bulbasaur' (both slot values registered) "
            "should route to battle.intent at padacioso-high",
        )
        data = battle_msgs[0].data
        self.assertEqual((data.get("pokemon_a") or "").lower(), "pikachu")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "bulbasaur")
