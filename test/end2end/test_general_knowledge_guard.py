"""Regression coverage for the general-knowledge false-positive defect.

``{pokemon}`` is a free slot (no ``pokemon.entity`` gates it before this
fix; only ``pokemon_a``/``pokemon_b`` feed ``battle.intent``). Combined with
unanchored ``GetPokemonInfo`` templates such as ``(describe|who is|what
is) [the pokemon] {pokemon}``, general-knowledge questions with no mention
of Pokémon at all matched at padatious-HIGH and then
``_resolve_pokemon_name``'s fuzzy matcher (threshold >= 0.6) picked an
arbitrary pokedex entry and spoke it -- installing the skill broke
unrelated general queries assistant-wide.

The fix requires the literal noun "pokemon" on every previously-unanchored
``GetPokemonInfo`` template. These tests assert the four reported
false-positive utterances no longer match any pokepedia intent, and that
the legitimate anchored phrasings still do.
"""
from unittest import TestCase

from ._helpers import IntentRoutingMixin, SKILL_ID

_PADATIOUS_HIGH = ["ovos-padatious-pipeline-plugin-high"]


class TestGeneralKnowledgeGuard(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def _padatious_high_types(self, utterance):
        types = self._capture(utterance, _PADATIOUS_HIGH)
        return [t for t in types if t.startswith(f"{SKILL_ID}:")]

    def test_president_of_france_does_not_match(self):
        self.assertFalse(
            self._padatious_high_types("who is the president of france")
        )

    def test_eiffel_tower_does_not_match(self):
        self.assertFalse(
            self._padatious_high_types("describe the eiffel tower")
        )

    def test_weather_does_not_match(self):
        self.assertFalse(
            self._padatious_high_types("tell me about the weather")
        )

    def test_capital_of_spain_does_not_match(self):
        self.assertFalse(
            self._padatious_high_types("what is the capital of spain")
        )

    def test_weather_does_not_match_type_intent(self):
        self.assertFalse(
            self._padatious_high_types("what type is the weather")
        )

    def test_anchored_tell_me_about_still_matches(self):
        self._assert_intent(
            "tell me about the pokemon pikachu", "GetPokemonInfo",
            padatious=True,
        )

    def test_anchored_describe_still_matches(self):
        self._assert_intent(
            "describe the pokemon charizard", "GetPokemonInfo",
            padatious=True,
        )

    def test_bare_pokemon_slot_still_matches(self):
        self._assert_intent(
            "pokemon bulbasaur", "GetPokemonInfo", padatious=True
        )
