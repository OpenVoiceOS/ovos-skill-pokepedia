"""Entity-file registration coverage for ovos-skill-pokepedia battle.intent
(en-US).

locale/en-US/intents/pokemon_a.entity and pokemon_b.entity feed the
{pokemon_a}/{pokemon_b} slots of battle.intent. They reach the intent engine
through ovos-workshop auto-registration (no register_entity_file() call in
this skill's own code -- see ovos_skill_pokepedia/__init__.py and
test/test_entity_registration.py for the wiring-level coverage).

Run: pytest test/end2end/test_entity_constraints.py -v --timeout=180
"""
from unittest import TestCase

from ovoscope.routing import TALLY

from ._helpers import IntentRoutingMixin, intent_topic

_BATTLE_INTENT = intent_topic("battle")


class TestEntityConstraints(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_battle_in_list_routes_and_tags_both_slots(self):
        """A registered pair ("pikachu"/"bulbasaur") reaches battle.intent
        with both slots tagged correctly, confirming the full bus-routed
        path resolves and tags real slot values."""
        utterance = "who wins pikachu or bulbasaur"
        messages = self._messages(utterance)
        TALLY.assert_routed(utterance, _BATTLE_INTENT, [m.msg_type for m in messages])
        battle_msgs = [m for m in messages
                       if m.msg_type in {_BATTLE_INTENT, f"{_BATTLE_INTENT}.intent"}]
        data = battle_msgs[0].data
        self.assertEqual((data.get("pokemon_a") or "").lower(), "pikachu")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "bulbasaur")
