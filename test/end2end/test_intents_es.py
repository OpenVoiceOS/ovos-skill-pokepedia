"""Intent-routing coverage for es-ES.

Utterances are drawn from the es-ES locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: two Adapt keyword intents (``GetPokemonInfo``,
``GetPokemonType``) and the Padatious ``battle.intent``.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestEsIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "es-ES"

    def test_info_routes_through_adapt(self):
        self._assert_intent(
            "dime pikachu", "GetPokemonInfo", padatious=False
        )

    def test_type_routes_through_adapt(self):
        self._assert_intent(
            "tipo de charizard", "GetPokemonType", padatious=False
        )

    def test_battle_routes_through_padatious(self):
        self._assert_intent(
            "quién gana entre pikachu y bulbasaur", "battle.intent",
            padatious=True,
        )
