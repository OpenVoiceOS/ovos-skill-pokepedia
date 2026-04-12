"""Test suite for OVOS Pokémon Battle Assistant skill."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestTypeAdvantage:
    """Test type advantage calculations."""

    def test_fire_against_grass(self):
        from ovos_skill_pokepedia import get_type_advantage

        assert get_type_advantage("fire", "grass") == "molto efficace"

    def test_fire_against_water(self):
        from ovos_skill_pokepedia import get_type_advantage

        assert get_type_advantage("fire", "water") == "non molto efficace"

    def test_water_against_fire(self):
        from ovos_skill_pokepedia import get_type_advantage

        assert get_type_advantage("water", "fire") == "molto efficace"

    def test_neutral(self):
        from ovos_skill_pokepedia import get_type_advantage

        assert get_type_advantage("normal", "fire") == "neutro"


class TestFormatFunctions:
    """Test child-friendly formatting functions."""

    def test_format_stat_strong(self):
        from ovos_skill_pokepedia import format_stat_childfriendly

        result = format_stat_childfriendly("attack", 130)
        assert "fortissimo" in result

    def test_format_stat_weak(self):
        from ovos_skill_pokepedia import format_stat_childfriendly

        result = format_stat_childfriendly("attack", 30)
        assert "debole" in result

    def test_format_types_single(self):
        from ovos_skill_pokepedia import format_types_childfriendly

        result = format_types_childfriendly(["fire"])
        assert result == "Fuoco"

    def test_format_types_dual(self):
        from ovos_skill_pokepedia import format_types_childfriendly

        result = format_types_childfriendly(["fire", "flying"])
        assert "Fuoco" in result and "Volante" in result


class TestIntentHandlers:
    """Test intent handlers."""

    def test_handle_get_pokemon_info(self):
        with patch("ovos_skill_pokepedia.PokeAPIClient"):
            from ovos_skill_pokepedia import PokemonSkill

            skill = PokemonSkill()
            skill.api_client = MagicMock()

            mock_pokemon = MagicMock()
            mock_pokemon.name = "pikachu"
            mock_stat = MagicMock()
            mock_stat.stat.name = "attack"
            mock_stat.base_stat = 55
            mock_pokemon.stats = [mock_stat]
            mock_type = MagicMock()
            mock_type.type.name = "electric"
            mock_pokemon.types = [mock_type]

            skill.api_client.get_pokemon.return_value = mock_pokemon

            message = MagicMock()
            message.data = {"PokemonName": "pikachu"}

            skill.handle_get_pokemon_info(message)

            skill.speak_dialog.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
