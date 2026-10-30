"""Intent-routing coverage for fr-FR.

Utterances are drawn from the fr-FR locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: the ``get_pokemon_info``,
``get_pokemon_type`` and ``battle`` file intents.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestFrIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "fr-FR"

    def test_info_routes(self):
        self._assert_intent(
            "présente-moi le pokémon pikachu", "get_pokemon_info"
        )

    def test_type_routes(self):
        self._assert_intent(
            "quel est le type du pokémon charizard", "get_pokemon_type"
        )

    def test_battle_routes(self):
        self._assert_routes(
            "qui gagne entre pikachu et bulbasaur", "battle.intent"
        )

    def test_battle_speaks_after_match(self):
        self._assert_intent(
            "qui gagne entre pikachu et bulbasaur", "battle.intent"
        )
