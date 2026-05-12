"""Unit tests for helper modules of the OVOS Pokémon Battle Assistant skill.

End-to-end intent-routing coverage lives in ``test/end2end/`` and exercises
the skill via ovoscope's MiniCroft — these unit tests cover pure helpers
(type advantages, child-friendly formatting, fuzzy matcher, API client
constructor) where a live bus is unnecessary.
"""
import pytest


class TestTypeAdvantage:
    def test_fire_against_grass(self):
        from ovos_skill_pokepedia import get_type_advantage
        assert get_type_advantage("fire", "grass") == "very_effective"

    def test_fire_against_water(self):
        from ovos_skill_pokepedia import get_type_advantage
        assert get_type_advantage("fire", "water") == "not_effective"

    def test_water_against_fire(self):
        from ovos_skill_pokepedia import get_type_advantage
        assert get_type_advantage("water", "fire") == "very_effective"

    def test_neutral(self):
        from ovos_skill_pokepedia import get_type_advantage
        assert get_type_advantage("normal", "fire") == "neutral"

    def test_case_insensitive(self):
        from ovos_skill_pokepedia import get_type_advantage
        assert get_type_advantage("FIRE", "grass") == "very_effective"


class TestFormatFunctions:
    def test_format_stat_very_strong(self):
        from ovos_skill_pokepedia import format_stat_childfriendly
        assert format_stat_childfriendly(130) == "very_strong"

    def test_format_stat_strong(self):
        from ovos_skill_pokepedia import format_stat_childfriendly
        assert format_stat_childfriendly(110) == "strong"

    def test_format_stat_normal(self):
        from ovos_skill_pokepedia import format_stat_childfriendly
        assert format_stat_childfriendly(80) == "normal"

    def test_format_stat_weak(self):
        from ovos_skill_pokepedia import format_stat_childfriendly
        assert format_stat_childfriendly(60) == "weak"

    def test_format_stat_very_weak(self):
        from ovos_skill_pokepedia import format_stat_childfriendly
        assert format_stat_childfriendly(30) == "very_weak"

    def test_format_stat_boundaries(self):
        from ovos_skill_pokepedia import format_stat_childfriendly
        assert format_stat_childfriendly(120) == "very_strong"
        assert format_stat_childfriendly(100) == "strong"

    def test_format_types_single(self):
        from ovos_skill_pokepedia import format_types_childfriendly
        assert format_types_childfriendly(["fire"]) == ["fire"]

    def test_format_types_dual(self):
        from ovos_skill_pokepedia import format_types_childfriendly
        assert format_types_childfriendly(["fire", "flying"]) == ["fire", "flying"]

    def test_format_types_normalizes_case(self):
        from ovos_skill_pokepedia import format_types_childfriendly
        assert format_types_childfriendly(["Fire", "Flying"]) == ["fire", "flying"]


class TestPokeAPIClientFactory:
    def test_create_returns_instance(self):
        from ovos_skill_pokepedia.api_client import create_api_client, PokeAPIClient
        client = create_api_client()
        assert isinstance(client, PokeAPIClient)

    def test_get_pokemon_strips_slot_whitespace(self, monkeypatch):
        from ovos_skill_pokepedia.api_client import PokeAPIClient
        import ovos_skill_pokepedia.api_client as api_client

        requested = []

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"name": "pikachu"}

        def fake_get(url, timeout):
            requested.append((url, timeout))
            return Response()

        monkeypatch.setattr(api_client.requests, "get", fake_get)

        assert PokeAPIClient().get_pokemon(" Pikachu ") == {"name": "pikachu"}
        assert requested == [
            ("https://pokeapi.co/api/v2/pokemon/pikachu", PokeAPIClient.TIMEOUT)
        ]


class TestFuzzyMatch:
    """Fuzzy name resolution now uses ovos_utils.parse.match_one directly —
    no PokemonFuzzyMatcher helper class. These tests document the contract
    the skill's _resolve_pokemon_name relies on."""

    NAMES = ["pikachu", "charizard", "bulbasaur", "squirtle"]

    def test_exact_match(self):
        from ovos_utils.parse import match_one
        best, score = match_one("pikachu", self.NAMES)
        assert best == "pikachu"
        assert score == 1.0

    def test_fuzzy_misspelling(self):
        from ovos_utils.parse import match_one
        best, score = match_one("charzard", self.NAMES)
        assert best == "charizard"
        assert score > 0.6

    def test_unrelated_name_low_score(self):
        from ovos_utils.parse import match_one
        _, score = match_one("xyzqqqq", self.NAMES)
        assert score < 0.6


class _FakeResources:
    def __init__(self, files):
        self.files = files

    def load_named_value_file(self, name):
        return self.files.get(name, {})


class TestSkillLocalizationHelpers:
    @staticmethod
    def _make_skill(files, names=None, lang="fr-FR"):
        from ovos_skill_pokepedia import PokemonSkill

        class Harness:
            _load_name_aliases = PokemonSkill._load_name_aliases
            _localized_pokemon_name = PokemonSkill._localized_pokemon_name
            _resolve_pokemon_name = PokemonSkill._resolve_pokemon_name
            _phrase = PokemonSkill._phrase
            _format_types = PokemonSkill._format_types
            _join_for_speech = PokemonSkill._join_for_speech

            def __init__(self):
                self.resources = _FakeResources(files)
                self.lang = lang

            def voc_list(self, name):
                return names or []

        return Harness()

    def test_resolve_french_name_to_api_slug(self):
        skill = self._make_skill(
            {"pokemon.name.aliases": {"salamèche": "charmander"}},
            ["charmander", "salamèche"],
        )

        assert skill._resolve_pokemon_name("salamèche") == "charmander"

    def test_resolve_name_strips_slot_whitespace(self):
        skill = self._make_skill({}, ["pikachu"])

        assert skill._resolve_pokemon_name(" Pikachu ") == "pikachu"

    def test_localized_display_name(self):
        skill = self._make_skill(
            {"pokemon.name.display": {"charmander": "Salamèche"}}
        )

        assert skill._localized_pokemon_name("charmander") == "Salamèche"

    def test_format_types_uses_type_specific_phrase(self):
        skill = self._make_skill(
            {
                "phrases": {
                    "normal": "correcte",
                    "normal_type": "Normal",
                    "flying_type": "Vol",
                    "list_conjunction": "et",
                }
            }
        )

        assert skill._format_types(["normal", "flying"]) == "Normal et Vol"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
