"""Unit tests for helper modules of the OVOS Pokémon Battle Assistant skill.

End-to-end intent-routing coverage lives in ``test/end2end/`` and exercises
the skill via ovoscope's MiniCroft — these unit tests cover pure helpers
(type advantages, child-friendly formatting, fuzzy matcher, API client
constructor) where a live bus is unnecessary.
"""
import json
from pathlib import Path

import pytest
from ovos_workshop.resource_files import SkillResources


PACKAGE_DIR = Path(__file__).parents[1] / "ovos_skill_pokepedia"
LOCALE_DIR = PACKAGE_DIR / "locale"
NAMES_DIR = PACKAGE_DIR / "data" / "pokemon_names"


def _dialog_text(lang, key):
    return (LOCALE_DIR / lang / "dialog" / f"{key}.dialog").read_text(
        encoding="utf-8"
    ).strip()


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


class TestSkillLocalizationHelpers:
    @staticmethod
    def _make_skill(names=None, lang="fr-FR"):
        from ovos_skill_pokepedia import PokemonSkill

        class Harness:
            _name_table = PokemonSkill._name_table
            _load_name_aliases = PokemonSkill._load_name_aliases
            _localized_pokemon_name = PokemonSkill._localized_pokemon_name
            _resolve_pokemon_name = PokemonSkill._resolve_pokemon_name
            _phrase = PokemonSkill._phrase
            _format_types = PokemonSkill._format_types
            _join_for_speech = PokemonSkill._join_for_speech

            def __init__(self):
                self.dialog_renderer = SkillResources(
                    str(PACKAGE_DIR), lang
                ).dialog_renderer
                self.lang = lang

            def voc_list(self, name):
                return names or []

        return Harness()

    def test_resolve_french_name_to_api_slug(self):
        skill = self._make_skill(["charmander", "salamèche"])

        assert skill._resolve_pokemon_name("salamèche") == "charmander"

    def test_resolve_name_strips_slot_whitespace(self):
        skill = self._make_skill(["pikachu"])

        assert skill._resolve_pokemon_name(" Pikachu ") == "pikachu"

    def test_localized_display_name(self):
        skill = self._make_skill()

        assert skill._localized_pokemon_name("charmander") == "Salamèche"

    def test_format_types_uses_type_specific_phrase(self):
        skill = self._make_skill()

        assert skill._format_types(["normal", "flying"]) == (
            f"{_dialog_text('fr-FR', 'normal_type')} "
            f"{_dialog_text('fr-FR', 'list_conjunction')} "
            f"{_dialog_text('fr-FR', 'flying_type')}"
        )

    @pytest.mark.parametrize(
        ("lang", "expected"),
        [
            ("es-ES", "Normal y Volador"),
            ("it-IT", "Normale e Volante"),
            ("pt-PT", "Normal e Voador"),
        ],
    )
    def test_format_types_avoids_normal_stat_collision_in_other_locales(
        self, lang, expected
    ):
        skill = self._make_skill(lang=lang)

        assert skill._format_types(["normal", "flying"]) == expected

    def test_resolve_name_uses_shared_aliases_without_language_table(self):
        skill = self._make_skill(["pikachu", "charizard"], lang="es-ES")

        assert skill._resolve_pokemon_name("charzard") == "charizard"
        assert skill._resolve_pokemon_name("mr mime") == "mr-mime"

    def test_display_name_without_language_table_falls_back_to_canonical_title(self):
        skill = self._make_skill(lang="it-IT")

        assert skill._localized_pokemon_name("mr-mime") == "Mr Mime"

    @pytest.mark.parametrize("lang", ["fr", "fr-FR", "fr-CA"])
    def test_language_table_resolves_regional_variants(self, lang):
        skill = self._make_skill(lang=lang)

        assert skill._localized_pokemon_name("bulbasaur") == "Bulbizarre"

    @pytest.mark.parametrize(
        ("lang", "key"),
        [
            ("en-US", "very_strong"),
            ("en-US", "fire"),
            ("fr-FR", "very_strong"),
            ("fr-FR", "list_conjunction"),
        ],
    )
    def test_phrase_returns_dialog_file_text(self, lang, key):
        skill = self._make_skill(lang=lang)

        assert skill._phrase(key) == _dialog_text(lang, key)

    def test_phrase_without_dialog_returns_bare_key(self):
        skill = self._make_skill(lang="en-US")

        assert skill._phrase("no_such_key") == "no_such_key"

    @pytest.mark.parametrize("name", ["bulbizarre", "salamèche"])
    def test_french_alias_lookup_matches_json(self, name):
        table = json.loads((NAMES_DIR / "fr-FR.json").read_text(encoding="utf-8"))
        skill = self._make_skill(lang="fr-FR")

        assert skill._load_name_aliases()[name] == table["aliases"][name]

    @pytest.mark.parametrize("slug", ["bulbasaur", "charmander"])
    def test_french_display_lookup_matches_json(self, slug):
        table = json.loads((NAMES_DIR / "fr-FR.json").read_text(encoding="utf-8"))
        skill = self._make_skill(lang="fr-FR")

        assert skill._localized_pokemon_name(slug) == table["display"][slug]

    def test_shared_aliases_match_json(self):
        shared = json.loads((NAMES_DIR / "aliases.json").read_text(encoding="utf-8"))
        skill = self._make_skill(lang="en-US")

        assert skill._load_name_aliases() == {
            alias.casefold(): slug for alias, slug in shared.items()
        }


class TestResourceRoles:
    def test_no_value_files_under_locale(self):
        assert sorted(LOCALE_DIR.rglob("*.value")) == []

    def test_every_dialog_base_name_is_compliant(self):
        import re

        names = [p.stem for p in LOCALE_DIR.rglob("*.dialog")]
        assert names
        assert [n for n in names if not re.fullmatch(r"[a-z0-9_]+", n)] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
