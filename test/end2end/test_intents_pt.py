"""Intent-routing coverage for pt-PT."""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestPtIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "pt-PT"

    # --- GetPokemonInfo ----------------------------------------------------
    def test_info_fala_me_de(self):
        self._assert_intent("fala-me de pikachu", "GetPokemonInfo")

    def test_info_diz_me_tudo_sobre(self):
        self._assert_intent("diz-me tudo sobre pikachu", "GetPokemonInfo")

    def test_info_o_que_e(self):
        self._assert_intent("o que é pikachu", "GetPokemonInfo")

    def test_info_descreve(self):
        self._assert_intent("descreve pikachu", "GetPokemonInfo")

    def test_info_info(self):
        self._assert_intent("info pikachu", "GetPokemonInfo")

    def test_info_diz_me(self):
        self._assert_intent("diz-me pikachu", "GetPokemonInfo")

    def test_info_tudo(self):
        self._assert_intent("tudo pikachu", "GetPokemonInfo")

    def test_info_conta_me_sobre(self):
        self._assert_intent("conta-me sobre pikachu", "GetPokemonInfo")

    # --- GetPokemonMoves ---------------------------------------------------
    def test_moves_que_ataques_tem(self):
        self._assert_intent("que ataques tem pikachu", "GetPokemonMoves")

    def test_moves_ataques(self):
        self._assert_intent("ataques pikachu", "GetPokemonMoves")

    def test_moves_movimentos(self):
        self._assert_intent("movimentos pikachu", "GetPokemonMoves")

    def test_moves_que_movimentos(self):
        self._assert_intent("que movimentos pikachu", "GetPokemonMoves")

    def test_moves_lista_de_ataques(self):
        self._assert_intent("lista de ataques pikachu", "GetPokemonMoves")

    # --- GetPokemonType ----------------------------------------------------
    def test_type_que_tipo_e(self):
        self._assert_intent("que tipo é pikachu", "GetPokemonType")

    def test_type_tipo(self):
        self._assert_intent("tipo pikachu", "GetPokemonType")

    def test_type_tipos(self):
        self._assert_intent("tipos pikachu", "GetPokemonType")

    def test_type_de_que_tipo(self):
        self._assert_intent("de que tipo pikachu", "GetPokemonType")

    def test_type_qual_o_tipo_de(self):
        self._assert_intent("qual o tipo de pikachu", "GetPokemonType")

    # --- BattleComparison --------------------------------------------------
    def test_battle_quem_ganha_entre(self):
        self._assert_intent(
            "quem ganha entre pikachu e charmander", "battle.intent"
        )

    def test_battle_quem_ganharia(self):
        self._assert_intent(
            "quem ganharia pikachu contra charmander", "battle.intent"
        )

    def test_battle_vs(self):
        self._assert_intent("pikachu vs charmander", "battle.intent")

    def test_battle_contra(self):
        self._assert_intent("pikachu contra charmander", "battle.intent")

    def test_battle_batalha_entre(self):
        self._assert_intent(
            "batalha entre pikachu e charmander", "battle.intent"
        )

    def test_battle_combate_entre(self):
        self._assert_intent(
            "combate entre pikachu e charmander", "battle.intent"
        )

    def test_battle_compara_e(self):
        self._assert_intent("compara pikachu e charmander", "battle.intent")

    def test_battle_quem_e_mais_forte(self):
        self._assert_intent(
            "quem é mais forte pikachu ou charmander", "battle.intent"
        )
