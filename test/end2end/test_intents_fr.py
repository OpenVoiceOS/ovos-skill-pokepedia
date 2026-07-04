"""Intent-routing coverage for fr-FR.

Utterances are drawn from the fr-FR locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: two Adapt keyword intents (``GetPokemonInfo``,
``GetPokemonType``) and the Padatious ``battle.intent``.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestFrIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "fr-FR"

    def test_info_routes_through_adapt(self):
        self._assert_intent(
            "parle-moi de pikachu", "GetPokemonInfo", padatious=False
        )

    def test_type_routes_through_adapt(self):
        self._assert_intent(
            "quel est le type de charizard", "GetPokemonType", padatious=False
        )

    def test_battle_routes_through_padatious(self):
        self._assert_intent(
            "qui gagne entre pikachu et bulbasaur", "battle.intent",
            padatious=True,
        )
