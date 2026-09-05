"""Intent-routing coverage for es-ES.

Utterances are drawn from the es-ES locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: the Padatious ``GetPokemonInfo`` and
``GetPokemonType`` intents and the Padatious ``battle.intent``.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestEsIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "es-ES"

    def test_info_routes_through_padatious(self):
        self._assert_intent(
            "describe el pokemon pikachu", "GetPokemonInfo", padatious=True
        )

    def test_type_routes_through_padatious(self):
        self._assert_intent(
            "tipo del pokemon charizard", "GetPokemonType", padatious=True
        )

    def test_battle_routes_through_padatious(self):
        self._assert_routes(
            "quién gana entre pikachu y bulbasaur", "battle.intent",
            padatious=True,
        )

    def test_battle_speaks_after_padatious_match(self):
        self._assert_intent(
            "quién gana entre pikachu y bulbasaur", "battle.intent",
            padatious=True,
        )
