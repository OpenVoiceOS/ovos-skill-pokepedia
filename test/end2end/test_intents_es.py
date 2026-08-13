"""Intent-routing coverage for es-ES.

Utterances are drawn from the es-ES locale files (``tell_me.voc``,
``type.voc``, ``battle.intent``), not machine-translated from English. Same
three intent families as en-US: two Adapt keyword intents (``GetPokemonInfo``,
``GetPokemonType``) and the Padatious ``battle.intent``.
"""
from unittest import TestCase

import pytest

from ._helpers import IntentRoutingMixin


class TestEsIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "es-ES"

    def test_info_routes_through_adapt(self):
        self._assert_intent(
            "dime pikachu", "GetPokemonInfo", padatious=False
        )

    def test_type_routes_through_adapt(self):
        self._assert_intent(
            "tipo de charizard", "GetPokemonType", padatious=False
        )

    def test_battle_routes_through_padatious(self):
        self._assert_routes(
            "quién gana entre pikachu y bulbasaur", "battle.intent",
            padatious=True,
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
            "quién gana entre pikachu y bulbasaur", "battle.intent",
            padatious=True,
        )
