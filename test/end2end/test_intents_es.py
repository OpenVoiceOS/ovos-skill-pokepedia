"""Intent-routing coverage for es-ES."""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestEsIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "es-ES"

    # --- GetPokemonInfo ----------------------------------------------------
    def test_info_dime_de(self):
        self._assert_intent("dime de pikachu", "GetPokemonInfo")

    def test_info_dime_todo_sobre(self):
        self._assert_intent("dime todo sobre pikachu", "GetPokemonInfo")

    def test_info_que_es(self):
        self._assert_intent("qué es pikachu", "GetPokemonInfo")

    def test_info_describe(self):
        self._assert_intent("describe pikachu", "GetPokemonInfo")

    def test_info_info(self):
        self._assert_intent("info pikachu", "GetPokemonInfo")

    def test_info_dime(self):
        self._assert_intent("dime pikachu", "GetPokemonInfo")

    def test_info_todo(self):
        self._assert_intent("todo pikachu", "GetPokemonInfo")

    # --- GetPokemonMoves ---------------------------------------------------
    def test_moves_que_movimientos_tiene(self):
        self._assert_intent("qué movimientos tiene pikachu", "GetPokemonMoves")

    def test_moves_movimientos(self):
        self._assert_intent("movimientos pikachu", "GetPokemonMoves")

    def test_moves_que_ataques(self):
        self._assert_intent("qué ataques pikachu", "GetPokemonMoves")

    def test_moves_conjunto_de_movimientos(self):
        self._assert_intent("conjunto de movimientos pikachu", "GetPokemonMoves")

    # --- GetPokemonType ----------------------------------------------------
    def test_type_que_tipo_es(self):
        self._assert_intent("qué tipo es pikachu", "GetPokemonType")

    def test_type_tipo(self):
        self._assert_intent("tipo pikachu", "GetPokemonType")

    def test_type_tipos(self):
        self._assert_intent("tipos pikachu", "GetPokemonType")

    def test_type_de_que_tipo(self):
        self._assert_intent("de qué tipo pikachu", "GetPokemonType")

    # --- BattleComparison --------------------------------------------------
    def test_battle_quien_gana_entre(self):
        self._assert_intent(
            "quién gana entre pikachu y charmander", "battle.intent"
        )

    def test_battle_quien_ganaria(self):
        self._assert_intent(
            "quién ganaría pikachu contra charmander", "battle.intent"
        )

    def test_battle_combate_entre(self):
        self._assert_intent(
            "combate entre pikachu y charmander", "battle.intent"
        )

    def test_battle_lucha_entre(self):
        self._assert_intent(
            "lucha entre pikachu y charmander", "battle.intent"
        )

    def test_battle_vs(self):
        self._assert_intent("pikachu vs charmander", "battle.intent")

    def test_battle_contra(self):
        self._assert_intent("pikachu contra charmander", "battle.intent")

    def test_battle_comparar_y(self):
        self._assert_intent("comparar pikachu y charmander", "battle.intent")

    def test_battle_quien_es_mas_fuerte(self):
        self._assert_intent(
            "quién es más fuerte pikachu o charmander", "battle.intent"
        )
