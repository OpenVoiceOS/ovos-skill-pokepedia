"""Intent-routing coverage for fr-FR."""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestFrIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "fr-FR"

    # --- GetPokemonInfo ----------------------------------------------------
    def test_info_parle_moi_de(self):
        self._assert_intent("parle-moi de pikachu", "GetPokemonInfo")

    def test_info_nom_francais(self):
        self._assert_intent("parle-moi de bulbizarre", "GetPokemonInfo")

    def test_info_dis_moi_tout_sur(self):
        self._assert_intent("dis-moi tout sur pikachu", "GetPokemonInfo")

    def test_info_quest_ce_que(self):
        self._assert_intent("qu'est-ce que pikachu", "GetPokemonInfo")

    def test_info_decris(self):
        self._assert_intent("décris pikachu", "GetPokemonInfo")

    def test_info_info(self):
        self._assert_intent("info pikachu", "GetPokemonInfo")

    def test_info_dis_moi(self):
        self._assert_intent("dis-moi pikachu", "GetPokemonInfo")

    def test_info_tout(self):
        self._assert_intent("tout pikachu", "GetPokemonInfo")

    # --- GetPokemonMoves ---------------------------------------------------
    def test_moves_quels_moves(self):
        self._assert_intent("quels moves pikachu", "GetPokemonMoves")

    def test_moves_moves(self):
        self._assert_intent("moves pikachu", "GetPokemonMoves")

    def test_moves_quelles_attaques(self):
        self._assert_intent("quelles attaques pikachu", "GetPokemonMoves")

    def test_moves_quelle_attaque_a_variant(self):
        self._assert_intent("quelle attaque à bulbizar", "GetPokemonMoves")

    def test_moves_quelles_attaques_a_variant(self):
        self._assert_intent("quelles attaques a bulbizzare", "GetPokemonMoves")

    def test_moves_quelles_capacites(self):
        self._assert_intent("quelles capacités salamèche", "GetPokemonMoves")

    def test_moves_moveset(self):
        self._assert_intent("moveset pikachu", "GetPokemonMoves")

    # --- GetPokemonType ----------------------------------------------------
    def test_type_quel_type_est(self):
        self._assert_intent("quel type est pikachu", "GetPokemonType")

    def test_type_type(self):
        self._assert_intent("type pikachu", "GetPokemonType")

    def test_type_types(self):
        self._assert_intent("types pikachu", "GetPokemonType")

    def test_type_de_quel_type(self):
        self._assert_intent("de quel type pikachu", "GetPokemonType")

    def test_type_nom_francais(self):
        self._assert_intent("quel est le type de carapuce", "GetPokemonType")

    # --- BattleComparison --------------------------------------------------
    def test_battle_qui_gagne_entre(self):
        self._assert_intent(
            "qui gagne entre pikachu et charmander", "battle.intent"
        )

    def test_battle_noms_francais(self):
        self._assert_intent(
            "qui gagne entre bulbizarre et salamèche", "battle.intent"
        )

    def test_battle_qui_lemporte(self):
        self._assert_intent(
            "qui l'emporte entre carapuce et salamèche", "battle.intent"
        )

    def test_battle_qui_gagnerait(self):
        self._assert_intent(
            "qui gagnerait pikachu contre charmander", "battle.intent"
        )

    def test_battle_combat_entre(self):
        self._assert_intent(
            "combat entre pikachu et charmander", "battle.intent"
        )

    def test_battle_vs(self):
        self._assert_intent("pikachu vs charmander", "battle.intent")

    def test_battle_contre(self):
        self._assert_intent("pikachu contre charmander", "battle.intent")

    def test_battle_comparer_et(self):
        self._assert_intent("comparer pikachu et charmander", "battle.intent")

    def test_battle_qui_est_plus_fort(self):
        self._assert_intent(
            "qui est plus fort pikachu ou charmander", "battle.intent"
        )
