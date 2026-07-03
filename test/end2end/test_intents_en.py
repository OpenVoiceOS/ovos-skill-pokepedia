"""Intent-routing coverage for en-US.

Each test method exercises one canonical utterance and asserts the expected
Adapt intent fires end-to-end. One method per utterance so failures pinpoint
the exact phrasing that does not route.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestEnIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    # --- GetPokemonInfo (tell_me + pokemon) --------------------------------
    def test_info_tell_me_about(self):
        self._assert_intent("tell me about pikachu", "GetPokemonInfo")

    def test_info_tell_me_everything_about(self):
        self._assert_intent("tell me everything about pikachu", "GetPokemonInfo")

    def test_info_what_is(self):
        self._assert_intent("what is pikachu", "GetPokemonInfo")

    def test_info_describe(self):
        self._assert_intent("describe pikachu", "GetPokemonInfo")

    def test_info_info(self):
        self._assert_intent("info pikachu", "GetPokemonInfo")

    def test_info_tell_me(self):
        self._assert_intent("tell me pikachu", "GetPokemonInfo")

    def test_info_everything(self):
        self._assert_intent("everything pikachu", "GetPokemonInfo")

    # --- GetPokemonMoves ---------------------------------------------------
    def test_moves_what_moves_does(self):
        self._assert_intent("what moves does pikachu have", "GetPokemonMoves")

    def test_moves_moves(self):
        self._assert_intent("moves pikachu", "GetPokemonMoves")

    def test_moves_which_moves(self):
        self._assert_intent("which moves pikachu", "GetPokemonMoves")

    def test_moves_moveset(self):
        self._assert_intent("moveset pikachu", "GetPokemonMoves")

    # --- GetPokemonType ----------------------------------------------------
    def test_type_what_type_is(self):
        self._assert_intent("what type is pikachu", "GetPokemonType")

    def test_type_type(self):
        self._assert_intent("type pikachu", "GetPokemonType")

    def test_type_types(self):
        self._assert_intent("types pikachu", "GetPokemonType")

    def test_type_of_what_type(self):
        self._assert_intent("of what type pikachu", "GetPokemonType")

    # --- BattleComparison --------------------------------------------------
    def test_battle_who_wins_between(self):
        self._assert_intent(
            "who wins between pikachu and charmander", "battle.intent"
        )

    def test_battle_who_would_win_vs(self):
        self._assert_intent(
            "who would win pikachu vs charmander", "battle.intent"
        )

    def test_battle_battle_and(self):
        self._assert_intent("battle pikachu and charmander", "battle.intent")

    def test_battle_fight_between(self):
        self._assert_intent(
            "fight between pikachu and charmander", "battle.intent"
        )

    def test_battle_vs(self):
        self._assert_intent("pikachu vs charmander", "battle.intent")

    def test_battle_against(self):
        self._assert_intent("pikachu against charmander", "battle.intent")

    def test_battle_compare_and(self):
        self._assert_intent("compare pikachu and charmander", "battle.intent")

    def test_battle_who_is_stronger(self):
        self._assert_intent(
            "who is stronger pikachu or charmander", "battle.intent"
        )
