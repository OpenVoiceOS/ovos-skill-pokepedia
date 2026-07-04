"""Intent-routing coverage for it-IT.

Utterances are drawn from the it-IT locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: two Adapt keyword intents (``GetPokemonInfo``,
``GetPokemonType``) and the Padatious ``battle.intent``.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestItIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "it-IT"

    def test_info_routes_through_adapt(self):
        self._assert_intent(
            "parlami di pikachu", "GetPokemonInfo", padatious=False
        )

    def test_type_routes_through_adapt(self):
        self._assert_intent(
            "tipo di charizard", "GetPokemonType", padatious=False
        )

    def test_battle_routes_through_padatious(self):
        self._assert_intent(
            "chi vince tra pikachu e bulbasaur", "battle.intent",
            padatious=True,
        )
