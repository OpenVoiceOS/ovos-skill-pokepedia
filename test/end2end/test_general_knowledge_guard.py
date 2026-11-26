"""Regression coverage for the general-knowledge false-positive defect.

``{pokemon}`` is a free slot (no ``pokemon.entity`` gates it before this
fix; only ``pokemon_a``/``pokemon_b`` feed ``battle.intent``). Combined with
unanchored ``get_pokemon_info`` templates such as ``(describe|who is|what
is) [the pokemon] {pokemon}``, general-knowledge questions with no mention
of Pokémon at all matched the high tier and then
``_resolve_pokemon_name``'s fuzzy matcher (threshold >= 0.6) picked an
arbitrary pokedex entry and spoke it -- installing the skill broke
unrelated general queries assistant-wide.

The fix requires the literal noun "pokemon" on every previously-unanchored
``get_pokemon_info`` template. These tests assert the four reported
false-positive utterances no longer match any pokepedia intent, and that
the legitimate anchored phrasings still do.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin


class TestGeneralKnowledgeGuard(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_president_of_france_does_not_match(self):
        self._assert_no_intent("who is the president of france")

    def test_eiffel_tower_does_not_match(self):
        self._assert_no_intent("describe the eiffel tower")

    def test_weather_does_not_match(self):
        self._assert_no_intent("tell me about the weather")

    def test_capital_of_spain_does_not_match(self):
        self._assert_no_intent("what is the capital of spain")

    def test_weather_does_not_match_type_intent(self):
        self._assert_no_intent("what type is the weather")

    def test_anchored_tell_me_about_still_matches(self):
        self._assert_intent("tell me about the pokemon pikachu", "get_pokemon_info")

    def test_anchored_describe_still_matches(self):
        self._assert_intent("describe the pokemon charizard", "get_pokemon_info")

    def test_bare_pokemon_slot_still_matches(self):
        self._assert_intent("pokemon bulbasaur", "get_pokemon_info")
