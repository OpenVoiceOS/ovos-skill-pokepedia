"""Intent-routing coverage for pt-PT.

Utterances are drawn from the pt-PT locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: two Adapt keyword intents (``GetPokemonInfo``,
``GetPokemonType``) and the Padatious ``battle.intent``.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestPtIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "pt-PT"

    def test_info_routes_through_adapt(self):
        self._assert_intent(
            "fala-me de pikachu", "GetPokemonInfo", padatious=False
        )

    def test_type_routes_through_adapt(self):
        self._assert_intent(
            "tipo de charizard", "GetPokemonType", padatious=False
        )

    def test_battle_routes_through_padatious(self):
        self._assert_intent(
            "quem ganha entre pikachu e bulbasaur", "battle.intent",
            padatious=True,
        )
