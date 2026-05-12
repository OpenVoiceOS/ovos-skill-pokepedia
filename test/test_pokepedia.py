"""Unit tests for helper modules of the OVOS Pokémon Battle Assistant skill.

End-to-end intent-routing coverage lives in ``test/end2end/`` and exercises
the skill via ovoscope's MiniCroft — these unit tests cover pure helpers
(type advantages, child-friendly formatting, fuzzy matcher, API client
constructor) where a live bus is unnecessary.
"""
import csv
from pathlib import Path

import pytest


LOCALE_DIR = Path(__file__).parents[1] / "ovos_skill_pokepedia" / "locale"


def _load_phrases(lang):
    with (LOCALE_DIR / lang / "dialog" / "phrases.value").open(
        encoding="utf-8", newline=""
    ) as phrases_file:
        return {
            key.strip(): value.strip()
            for key, value in csv.reader(phrases_file)
            if key.strip()
        }


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

    def test_resolve_french_asr_variant_to_api_slug(self):
        skill = self._make_skill(
            {"pokemon.name.aliases": {"bulbizar": "bulbasaur"}},
            ["bulbasaur", "bulbizarre", "bulbizar"],
        )

        assert skill._resolve_pokemon_name("bulbizar") == "bulbasaur"

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

    @pytest.mark.parametrize(
        ("lang", "phrases", "expected"),
        [
            (
                "es-ES",
                {
                    "normal": "ataque medio",
                    "normal_type": "Normal",
                    "flying": "Volador",
                },
                "Normal y Volador",
            ),
            (
                "it-IT",
                {
                    "normal": "attacco medio",
                    "normal_type": "Normale",
                    "flying": "Volante",
                },
                "Normale e Volante",
            ),
            (
                "pt-PT",
                {"normal": "ataque médio", "normal_type": "Normal", "flying": "Voador"},
                "Normal e Voador",
            ),
        ],
    )
    def test_format_types_avoids_normal_stat_collision_in_other_locales(
        self, lang, phrases, expected
    ):
        skill = self._make_skill({"phrases": phrases}, lang=lang)

        assert skill._format_types(["normal", "flying"]) == expected

    def test_resolve_name_without_alias_file_uses_existing_vocab(self):
        skill = self._make_skill({}, ["pikachu", "charizard"], lang="es-ES")

        assert skill._resolve_pokemon_name("charzard") == "charizard"

    def test_display_name_without_locale_file_falls_back_to_canonical_title(self):
        skill = self._make_skill({}, lang="it-IT")

        assert skill._localized_pokemon_name("mr-mime") == "Mr Mime"

    @pytest.mark.parametrize(
        ("lang", "expected"),
        [("es-ES", "Normal"), ("it-IT", "Normale"), ("pt-PT", "Normal")],
    )
    def test_non_french_phrase_files_distinguish_normal_type(self, lang, expected):
        phrases = _load_phrases(lang)

        assert phrases["normal_type"] == expected
        assert phrases["normal_type"] != phrases["normal"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
