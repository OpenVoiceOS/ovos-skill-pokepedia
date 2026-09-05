"""Intent-routing coverage for fr-FR.

Utterances are drawn from the fr-FR locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: the Padatious ``GetPokemonInfo`` and
``GetPokemonType`` intents and the Padatious ``battle.intent``.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestFrIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "fr-FR"

    def test_info_routes_through_padatious(self):
        self._assert_intent(
            "présente-moi le pokémon pikachu", "GetPokemonInfo", padatious=True
        )

    def test_type_routes_through_padatious(self):
        self._assert_intent(
            "quel est le type du pokémon charizard", "GetPokemonType", padatious=True
        )

    def test_battle_routes_through_padatious(self):
        self._assert_routes(
            "qui gagne entre pikachu et bulbasaur", "battle.intent",
            padatious=True,
        )

    def test_battle_speaks_after_padatious_match(self):
        self._assert_intent(
            "qui gagne entre pikachu et bulbasaur", "battle.intent",
            padatious=True,
        )
