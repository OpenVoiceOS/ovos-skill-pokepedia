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

    def test_info_donne_moi_des_infos_sur(self):
        self._assert_intent("donne-moi des infos sur pikachu", "GetPokemonInfo")

    def test_info_quest_ce_que_le_pokemon(self):
        self._assert_intent(
            "qu'est-ce que le pokémon pikachu", "GetPokemonInfo"
        )

    def test_info_decris(self):
        self._assert_intent("décris pikachu", "GetPokemonInfo")

    def test_info_decris_le_pokemon(self):
        self._assert_intent("décris le pokémon pikachu", "GetPokemonInfo")

    def test_info_presente_moi_le_pokemon(self):
        self._assert_intent("présente-moi le pokémon pikachu", "GetPokemonInfo")

    def test_info_qui_est_le_pokemon(self):
        self._assert_intent("qui est le pokémon pikachu", "GetPokemonInfo")

    # --- GetPokemonMoves ---------------------------------------------------
    def test_moves_quelles_sont_les_capacites_de(self):
        self._assert_intent(
            "quelles sont les capacités de pikachu", "GetPokemonMoves"
        )

    def test_moves_donne_moi_les_capacites_de(self):
        self._assert_intent(
            "donne-moi les capacités de pikachu", "GetPokemonMoves"
        )

    def test_moves_quelles_attaques(self):
        self._assert_intent("quelles attaques pikachu", "GetPokemonMoves")

    def test_moves_quelle_attaque_a_variant(self):
        self._assert_intent("quelle attaque à bulbizar", "GetPokemonMoves")

    def test_moves_quelles_attaques_a_variant(self):
        self._assert_intent("quelles attaques a bulbizzare", "GetPokemonMoves")

    def test_moves_quelles_capacites(self):
        self._assert_intent("quelles capacités salamèche", "GetPokemonMoves")

    def test_moves_quelles_capacites_peut_apprendre(self):
        self._assert_intent(
            "quelles capacités peut apprendre bulbizarre", "GetPokemonMoves"
        )

    def test_moves_moveset(self):
        self._assert_intent("moveset de pikachu", "GetPokemonMoves")

    # --- GetPokemonType ----------------------------------------------------
    def test_type_quel_type_de_pokemon_est(self):
        self._assert_intent(
            "quel type de pokémon est pikachu", "GetPokemonType"
        )

    def test_type_quel_type_de_pokemon_est_ascii(self):
        self._assert_intent(
            "quel type de pokemon est pikachu", "GetPokemonType"
        )

    def test_type_type_du_pokemon(self):
        self._assert_intent("type du pokémon pikachu", "GetPokemonType")

    def test_type_types_du_pokemon(self):
        self._assert_intent("types du pokemon pikachu", "GetPokemonType")

    def test_type_de_quel_type_est(self):
        self._assert_intent("de quel type est pikachu", "GetPokemonType")

    def test_type_est_de_quel_type(self):
        self._assert_intent("pikachu est de quel type", "GetPokemonType")

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

    def test_battle_qui_gagnerait_dans_un_combat(self):
        self._assert_intent(
            "qui gagnerait dans un combat entre pikachu et charmander",
            "battle.intent",
        )

    def test_battle_qui_a_lavantage(self):
        self._assert_intent(
            "qui a l'avantage entre pikachu et charmander", "battle.intent"
        )

    def test_battle_lequel_est_le_plus_fort(self):
        self._assert_intent(
            "lequel est le plus fort entre pikachu et charmander",
            "battle.intent",
        )

    def test_battle_combat_entre(self):
        self._assert_intent(
            "combat entre pikachu et charmander", "battle.intent"
        )

    def test_battle_combat_pokemon_entre(self):
        self._assert_intent(
            "combat pokémon entre pikachu et charmander", "battle.intent"
        )

    def test_battle_vs(self):
        self._assert_intent("pikachu vs charmander", "battle.intent")

    def test_battle_contre(self):
        self._assert_intent("pikachu contre charmander", "battle.intent")

    def test_battle_comparer_et(self):
        self._assert_intent("comparer pikachu et charmander", "battle.intent")

    def test_battle_compare_les_pokemon(self):
        self._assert_intent(
            "compare les pokémon pikachu et charmander", "battle.intent"
        )

    def test_battle_qui_est_plus_fort(self):
        self._assert_intent(
            "qui est plus fort pikachu ou charmander", "battle.intent"
        )

    # --- Broad prompt collision checks -------------------------------------
    def test_no_broad_info(self):
        self._assert_no_intent("info pikachu")

    def test_no_broad_dis_moi(self):
        self._assert_no_intent("dis-moi pikachu")

    def test_no_broad_type(self):
        self._assert_no_intent("type pikachu")

    def test_no_broad_quel_type_est(self):
        self._assert_no_intent("quel type est pikachu")
