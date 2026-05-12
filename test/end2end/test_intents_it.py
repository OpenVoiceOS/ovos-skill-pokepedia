"""Intent-routing coverage for it-IT."""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestItIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "it-IT"

    # --- GetPokemonInfo ----------------------------------------------------
    def test_info_descrivi(self):
        self._assert_intent("descrivi pikachu", "GetPokemonInfo")

    def test_info_dimmi_qualcosa_su(self):
        self._assert_intent("dimmi qualcosa su pikachu", "GetPokemonInfo")

    def test_info_dimmi_tutto_su(self):
        self._assert_intent("dimmi tutto su pikachu", "GetPokemonInfo")

    def test_info_informazioni(self):
        self._assert_intent("informazioni pikachu", "GetPokemonInfo")

    def test_info_cosa_e(self):
        self._assert_intent("cosa è pikachu", "GetPokemonInfo")

    def test_info_dimmi(self):
        self._assert_intent("dimmi pikachu", "GetPokemonInfo")

    # --- GetPokemonMoves ---------------------------------------------------
    def test_moves_quali_mosse_ha(self):
        self._assert_intent("quali mosse ha pikachu", "GetPokemonMoves")

    def test_moves_mosse(self):
        self._assert_intent("mosse pikachu", "GetPokemonMoves")

    def test_moves_quali_mosse(self):
        self._assert_intent("quali mosse pikachu", "GetPokemonMoves")

    def test_moves_set_mosse(self):
        self._assert_intent("set mosse pikachu", "GetPokemonMoves")

    def test_moves_move(self):
        self._assert_intent("move pikachu", "GetPokemonMoves")

    def test_moves_movimento(self):
        self._assert_intent("movimento pikachu", "GetPokemonMoves")

    def test_moves_attacchi(self):
        self._assert_intent("attacchi pikachu", "GetPokemonMoves")

    # --- GetPokemonType ----------------------------------------------------
    def test_type_che_tipo_e(self):
        self._assert_intent("che tipo è pikachu", "GetPokemonType")

    def test_type_tipo(self):
        self._assert_intent("tipo pikachu", "GetPokemonType")

    def test_type_tipi(self):
        self._assert_intent("tipi pikachu", "GetPokemonType")

    def test_type_di_che_tipo(self):
        self._assert_intent("di che tipo pikachu", "GetPokemonType")

    # --- BattleComparison --------------------------------------------------
    def test_battle_chi_vince_tra(self):
        self._assert_intent(
            "chi vince tra pikachu e charmander", "battle.intent"
        )

    def test_battle_battaglia_tra(self):
        self._assert_intent(
            "battaglia tra pikachu e charmander", "battle.intent"
        )

    def test_battle_combattimento_tra(self):
        self._assert_intent(
            "combattimento tra pikachu e charmander", "battle.intent"
        )

    def test_battle_vs(self):
        self._assert_intent("pikachu vs charmander", "battle.intent")

    def test_battle_contro(self):
        self._assert_intent("pikachu contro charmander", "battle.intent")

    def test_battle_confronta_e(self):
        self._assert_intent("confronta pikachu e charmander", "battle.intent")

    def test_battle_chi_e_piu_forte(self):
        self._assert_intent(
            "chi è più forte pikachu o charmander", "battle.intent"
        )

    def test_battle_chi_vincerebbe(self):
        self._assert_intent(
            "chi vincerebbe pikachu contro charmander", "battle.intent"
        )
