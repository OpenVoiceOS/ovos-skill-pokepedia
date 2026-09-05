"""Stress test for battle.intent's two-value capture: does a single utterance
naming two Pokémon populate BOTH {pokemon_a} and {pokemon_b} distinctly,
across separators, word order, and multi-word names?

Run: pytest test/end2end/test_battle_two_capture_stress.py -v --timeout=180
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin, SKILL_ID
from ovoscope import CaptureSession, make_session, make_utterance_message

HIGH = ["ovos-padatious-pipeline-plugin-high"]
_BATTLE_INTENT = f"{SKILL_ID}:battle"


class TestBattleTwoCaptureStress(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def _capture_slots(self, utterance):
        session = make_session(
            session_id="pokepedia-two-capture-stress",
            pipeline=HIGH,
            blacklisted_intents=[],
            blacklisted_skills=[],
            lang=self.LANG,
        )
        message = make_utterance_message(utterance, lang=self.LANG, session=session)
        cap = CaptureSession(minicroft=self.minicroft)
        cap.capture(message, timeout=20)
        messages = cap.finish()
        battle_msgs = [
            m for m in messages
            if m.msg_type in {_BATTLE_INTENT, f"{_BATTLE_INTENT}.intent"}
        ]
        self.assertTrue(battle_msgs, f"{utterance!r} did not route to battle.intent")
        return battle_msgs[0].data

    def test_who_wins_comma_separated(self):
        data = self._capture_slots("who wins, charmander or pikachu")
        self.assertEqual((data.get("pokemon_a") or "").lower(), "charmander")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "pikachu")

    def test_who_would_win_between(self):
        data = self._capture_slots("who would win between bulbasaur and squirtle")
        self.assertEqual((data.get("pokemon_a") or "").lower(), "bulbasaur")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "squirtle")

    def test_reversed_order_leading_pair(self):
        data = self._capture_slots("pikachu vs charizard who wins")
        self.assertEqual((data.get("pokemon_a") or "").lower(), "pikachu")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "charizard")

    def test_multiword_name_mr_mime(self):
        data = self._capture_slots("who wins mr mime or pikachu")
        self.assertEqual((data.get("pokemon_a") or "").lower().replace(" ", "-"), "mr-mime")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "pikachu")

    def test_distinct_slots_not_swapped_or_duplicated(self):
        data = self._capture_slots("who wins pikachu or charmander")
        a = (data.get("pokemon_a") or "").lower()
        b = (data.get("pokemon_b") or "").lower()
        self.assertNotEqual(a, b, "pokemon_a and pokemon_b captured the same value")
        self.assertEqual(a, "pikachu")
        self.assertEqual(b, "charmander")
