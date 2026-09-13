"""Intent-routing coverage for da-DK.

Utterances are taken from the da-DK locale files themselves, not translated
from English: the plural form comes from `GetPokemonType.intent`'s own
`hvilke typer` branch, which the file's earlier `hvilke(n)` spelling could
never produce.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestDaIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "da-DK"

    def test_info_routes_through_padatious(self):
        self._assert_intent(
            "beskriv pokemonen pikachu", "GetPokemonInfo", padatious=True
        )

    def test_type_singular_routes_through_padatious(self):
        self._assert_intent(
            "hvilken type har pokemonen charizard", "GetPokemonType",
            padatious=True,
        )

    def test_type_plural_routes_through_padatious(self):
        self._assert_intent(
            "hvilke typer har pokemonen charizard", "GetPokemonType",
            padatious=True,
        )

    def test_moves_routes_through_padatious(self):
        self._assert_intent(
            "hvilke angreb kan pikachu", "GetPokemonMoves", padatious=True
        )

    def test_battle_routes_through_padatious(self):
        self._assert_routes(
            "hvem vinder mellem pikachu og bulbasaur", "battle.intent",
            padatious=True,
        )
