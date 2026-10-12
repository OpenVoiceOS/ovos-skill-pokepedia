"""Intent-routing coverage for en-US.

One canonical utterance per intent family: the
``get_pokemon_info`` and ``get_pokemon_type`` file intents, and the
``battle.intent``. Each asserts the intent routed and the skill spoke — a
drift-immune subset, never an ordered message sequence.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestEnIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_info_routes_through_padacioso(self):
        self._assert_intent(
            "tell me about the pokemon pikachu", "get_pokemon_info", padacioso=True
        )

    def test_type_routes_through_padacioso(self):
        self._assert_intent(
            "what type is the pokemon charizard", "get_pokemon_type", padacioso=True
        )

    def test_battle_routes_through_padacioso(self):
        self._assert_routes(
            "who wins pikachu or bulbasaur", "battle.intent", padacioso=True
        )

    def test_battle_speaks_after_padacioso_match(self):
        self._assert_intent(
            "who wins pikachu or bulbasaur", "battle.intent", padacioso=True
        )
