"""Intent-routing coverage for it-IT.

Utterances are drawn from the it-IT locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: the ``get_pokemon_info`` and
``get_pokemon_type`` intents and ``battle.intent``, routed by padacioso.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestItIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "it-IT"

    def test_info_routes_through_padacioso(self):
        self._assert_intent(
            "descrivi il pokemon pikachu", "get_pokemon_info", padacioso=True
        )

    def test_type_routes_through_padacioso(self):
        self._assert_intent(
            "tipo del pokemon charizard", "get_pokemon_type", padacioso=True
        )

    def test_battle_routes_through_padacioso(self):
        self._assert_routes(
            "chi vince tra pikachu e bulbasaur", "battle.intent",
            padacioso=True,
        )

    def test_battle_speaks_after_padacioso_match(self):
        self._assert_intent(
            "chi vince tra pikachu e bulbasaur", "battle.intent",
            padacioso=True,
        )
