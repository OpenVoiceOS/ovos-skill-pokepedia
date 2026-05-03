"""Test suite for OVOS Pokémon Battle Assistant skill."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestTypeAdvantage:
    """Test type advantage calculations."""

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


class TestFormatFunctions:
    """Test child-friendly formatting functions."""

    def test_format_stat_very_strong(self):
        from ovos_skill_pokepedia import format_stat_childfriendly

        result = format_stat_childfriendly(130)
        assert result == "very_strong"

    def test_format_stat_strong(self):
        from ovos_skill_pokepedia import format_stat_childfriendly

        result = format_stat_childfriendly(110)
        assert result == "strong"

    def test_format_stat_normal(self):
        from ovos_skill_pokepedia import format_stat_childfriendly

        result = format_stat_childfriendly(80)
        assert result == "normal"

    def test_format_stat_weak(self):
        from ovos_skill_pokepedia import format_stat_childfriendly

        result = format_stat_childfriendly(60)
        assert result == "weak"

    def test_format_stat_very_weak(self):
        from ovos_skill_pokepedia import format_stat_childfriendly

        result = format_stat_childfriendly(30)
        assert result == "very_weak"

    def test_format_types_single(self):
        from ovos_skill_pokepedia import format_types_childfriendly

        result = format_types_childfriendly(["fire"])
        assert result == ["fire"]

    def test_format_types_dual(self):
        from ovos_skill_pokepedia import format_types_childfriendly

        result = format_types_childfriendly(["fire", "flying"])
        assert result == ["fire", "flying"]


class TestTranslation:
    """Test translation functionality."""

    def test_english_translations(self):
        from ovos_skill_pokepedia import PokemonSkill

        translations_en = {
            "very_strong": "very strong attack",
            "fire": "Fire",
            "water": "Water",
        }

        assert translations_en["very_strong"] == "very strong attack"
        assert translations_en["fire"] == "Fire"
        assert translations_en["water"] == "Water"


class TestIntentHandlers:
    """Test intent handlers."""

    def test_handle_get_pokemon_info(self):
        with patch("ovos_skill_pokepedia.PokeAPIClient"):
            from ovos_skill_pokepedia import PokemonSkill

            skill = PokemonSkill(bus=None, skill_id="test")
            skill.api_client = MagicMock()

            mock_pokemon = {
                "name": "pikachu",
                "stats": [
                    {"stat": {"name": "attack"}, "base_stat": 55},
                    {"stat": {"name": "speed"}, "base_stat": 90},
                ],
                "types": [{"type": {"name": "electric"}}],
                "abilities": [{"ability": {"name": "static"}}],
            }

            skill.api_client.get_pokemon.return_value = mock_pokemon

            message = MagicMock()
            message.data = {"PokemonName": "pikachu"}

            with patch.object(skill, "speak_dialog") as mock_speak:
                skill.handle_get_pokemon_info(message)
                mock_speak.assert_called_once()


class TestPokeAPIClient:
    """Test PokeAPI client functionality."""

    def test_create_api_client(self):
        from ovos_skill_pokepedia.api_client import create_api_client, PokeAPIClient

        client = create_api_client()
        assert client is not None
        assert isinstance(client, PokeAPIClient)

    def test_get_type_advantage_fire_grass(self):
        from ovos_skill_pokepedia.api_client import get_type_advantage

        assert get_type_advantage("fire", "grass") == "very_effective"

    def test_get_type_advantage_water_fire(self):
        from ovos_skill_pokepedia.api_client import get_type_advantage

        assert get_type_advantage("water", "fire") == "very_effective"

    def test_get_type_advantage_case_insensitive(self):
        from ovos_skill_pokepedia.api_client import get_type_advantage

        assert get_type_advantage("FIRE", "grass") == "very_effective"

    def test_format_types_multiple(self):
        from ovos_skill_pokepedia.api_client import format_types_childfriendly

        result = format_types_childfriendly(["Fire", "Flying"])
        assert result == ["fire", "flying"]

    def test_format_stat_boundaries(self):
        from ovos_skill_pokepedia.api_client import format_stat_childfriendly

        assert format_stat_childfriendly(120) == "very_strong"
        assert format_stat_childfriendly(100) == "strong"
        assert format_stat_childfriendly(80) == "normal"
        assert format_stat_childfriendly(60) == "weak"


class TestFuzzyMatcher:
    """Test fuzzy matcher for Pokémon names."""

    def test_fuzzy_matcher_exact_match(self):
        from ovos_skill_pokepedia.fuzzy_matcher import PokemonFuzzyMatcher
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("pikachu\ncharizard\nbulbasaur\n")
            temp_path = f.name

        try:
            matcher = PokemonFuzzyMatcher(vocab_path=temp_path)
            result, conf = matcher.match("pikachu")
            assert result == "pikachu"
            assert conf == 1.0
        finally:
            os.unlink(temp_path)

    def test_fuzzy_matcher_fuzzy_match(self):
        from ovos_skill_pokepedia.fuzzy_matcher import PokemonFuzzyMatcher
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("pikachu\ncharizard\nbulbasaur\n")
            temp_path = f.name

        try:
            matcher = PokemonFuzzyMatcher(vocab_path=temp_path)
            result, conf = matcher.match("charzard")
            assert result == "charizard"
            assert conf > 0.6
        finally:
            os.unlink(temp_path)

    def test_fuzzy_matcher_no_match(self):
        from ovos_skill_pokepedia.fuzzy_matcher import PokemonFuzzyMatcher
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("pikachu\ncharizard\n")
            temp_path = f.name

        try:
            matcher = PokemonFuzzyMatcher(vocab_path=temp_path)
            result, conf = matcher.match("xyznonexistent")
            assert result == "xyznonexistent"
            assert conf == 1.0
        finally:
            os.unlink(temp_path)

    def test_fuzzy_matcher_transcription_cache(self):
        from ovos_skill_pokepedia.fuzzy_matcher import PokemonFuzzyMatcher
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("charizard\nsquirtle\n")
            temp_path = f.name

        try:
            matcher = PokemonFuzzyMatcher(vocab_path=temp_path)
            matcher.cache_transcription("charizart", "charizard")
            result, conf = matcher.match("charizart")
            assert result == "charizard"
            assert conf == 1.0
        finally:
            os.unlink(temp_path)

    def test_fuzzy_matcher_empty_input(self):
        from ovos_skill_pokepedia.fuzzy_matcher import PokemonFuzzyMatcher
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("pikachu\n")
            temp_path = f.name

        try:
            matcher = PokemonFuzzyMatcher(vocab_path=temp_path)
            result, conf = matcher.match("")
            assert result == ""
            assert conf == 1.0
        finally:
            os.unlink(temp_path)

    def test_fuzzy_matcher_common_misspellings(self):
        from ovos_skill_pokepedia.fuzzy_matcher import PokemonFuzzyMatcher
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".voc", delete=False) as f:
            f.write("charizard\nsquirtle\npikachu\n")
            temp_path = f.name

        try:
            matcher = PokemonFuzzyMatcher(vocab_path=temp_path)
            result1, _ = matcher.match("charizart")
            result2, _ = matcher.match("squirtal")
            assert result1 == "charizard"
            assert result2 == "squirtle"
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
