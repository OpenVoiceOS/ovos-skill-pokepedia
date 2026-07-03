"""Intent-routing coverage for en-US.

One canonical utterance per intent family: an Adapt keyword intent
(``GetPokemonInfo``), a second Adapt intent (``GetPokemonType``), and the
Padatious file intent (``battle.intent``). Each asserts the intent routed and
the skill spoke — a drift-immune subset, never an ordered message sequence.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestEnIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_info_routes_through_adapt(self):
        self._assert_intent(
            "tell me about pikachu", "GetPokemonInfo", padatious=False
        )

    def test_type_routes_through_adapt(self):
        self._assert_intent(
            "what type is charizard", "GetPokemonType", padatious=False
        )

    def test_battle_routes_through_padatious(self):
        self._assert_intent(
            "who wins pikachu or bulbasaur", "battle.intent", padatious=True
        )
