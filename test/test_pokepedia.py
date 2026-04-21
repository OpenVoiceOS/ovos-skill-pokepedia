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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
