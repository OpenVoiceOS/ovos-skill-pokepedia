"""Intent-routing coverage for pt-PT.

Utterances are drawn from the pt-PT locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: the ``get_pokemon_info``,
``get_pokemon_type`` and ``battle`` file intents.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestPtIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "pt-PT"

    def test_info_routes(self):
        self._assert_intent(
            "descreve o pokemon pikachu", "get_pokemon_info"
        )

    def test_type_routes(self):
        self._assert_intent(
            "tipo do pokemon charizard", "get_pokemon_type"
        )

    def test_battle_routes(self):
        self._assert_routes(
            "quem ganha entre pikachu e bulbasaur", "battle.intent"
        )

    def test_battle_speaks_after_match(self):
        self._assert_intent(
            "quem ganha entre pikachu e bulbasaur", "battle.intent"
        )
