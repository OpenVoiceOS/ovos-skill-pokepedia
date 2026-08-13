"""Intent-routing coverage for en-US.

One canonical utterance per intent family: an Adapt keyword intent
(``GetPokemonInfo``), a second Adapt intent (``GetPokemonType``), and the
Padatious file intent (``battle.intent``). Each asserts the intent routed and
the skill spoke — a drift-immune subset, never an ordered message sequence.
"""
from unittest import TestCase

import pytest

from ._helpers import IntentRoutingMixin


class TestEnIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_info_routes_through_adapt(self):
        self._assert_intent(
            "tell me about pikachu", "GetPokemonInfo", padatious=False
        )

    def test_type_routes_through_adapt(self):
        self._assert_intent(
            "what type is charizard", "GetPokemonType", padatious=False
        )

    def test_battle_routes_through_padatious(self):
        self._assert_routes(
            "who wins pikachu or bulbasaur", "battle.intent", padatious=True
        )

    @pytest.mark.xfail(strict=True, reason=(
        "known gap (verified reproducible, independent of pipeline plugin): "
        "battle.intent routes correctly under real ovos-padatious (match_type "
        "observed as '<skill_id>:battle', the stripped name) but the handler "
        "body never runs. OVOSSkill.register_intent_file() binds the handler's "
        "bus listener under the '.intent'-suffixed event name "
        "('<skill_id>:battle.intent'), which the intent service never emits -- "
        "same class of gap as ovos-skill-ggwave's _HANDLER_BINDING_XFAIL. "
        "Routing itself (see test_battle_routes_through_padatious) is correct "
        "and passes."
    ))
    def test_battle_speaks_after_padatious_match(self):
        self._assert_intent(
            "who wins pikachu or bulbasaur", "battle.intent", padatious=True
        )
