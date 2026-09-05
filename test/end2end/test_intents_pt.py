"""Intent-routing coverage for pt-PT.

Utterances are drawn from the pt-PT locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: the Padatious ``GetPokemonInfo`` and
``GetPokemonType`` intents and the Padatious ``battle.intent``.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestPtIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "pt-PT"

    def test_info_routes_through_padatious(self):
        self._assert_intent(
            "descreve o pokemon pikachu", "GetPokemonInfo", padatious=True
        )

    def test_type_routes_through_padatious(self):
        self._assert_intent(
            "tipo do pokemon charizard", "GetPokemonType", padatious=True
        )

    def test_battle_routes_through_padatious(self):
        self._assert_routes(
            "quem ganha entre pikachu e bulbasaur", "battle.intent",
            padatious=True,
        )

    def test_battle_speaks_after_padatious_match(self):
        self._assert_intent(
            "quem ganha entre pikachu e bulbasaur", "battle.intent",
            padatious=True,
        )
