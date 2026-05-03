"""
PokeAPI client for Pokémon data fetching.
Extracted from main skill for better modularity and testability.
"""

import requests
from functools import lru_cache

from ovos_utils.log import LOG


class PokemonPokeAPIError(Exception):
    """Error when fetching Pokémon data from API fails."""

    pass


# Type advantage map - simplified for children
TYPE_ADVANTAGES = {
    "fire": {
        "weak_to": ["water", "ground", "rock"],
        "strong_against": ["grass", "ice", "bug", "steel"],
    },
    "water": {
        "weak_to": ["electric", "grass"],
        "strong_against": ["fire", "ground", "rock"],
    },
    "grass": {
        "weak_to": ["fire", "ice", "poison", "flying", "bug"],
        "strong_against": ["water", "ground", "rock"],
    },
    "electric": {"weak_to": ["ground", "grass"], "strong_against": ["water", "flying"]},
    "ice": {
        "weak_to": ["fire", "steel", "rock", "fighting"],
        "strong_against": ["grass", "ground", "flying", "dragon"],
    },
    "fighting": {
        "weak_to": ["flying", "psychic", "fairy"],
        "strong_against": ["normal", "ice", "rock", "dark", "steel"],
    },
    "poison": {"weak_to": ["ground", "psychic"], "strong_against": ["grass", "fairy"]},
    "ground": {
        "weak_to": ["water", "grass", "ice"],
        "strong_against": ["fire", "electric", "poison", "rock", "steel"],
    },
    "flying": {
        "weak_to": ["electric", "ice", "rock", "steel"],
        "strong_against": ["grass", "fighting", "bug"],
    },
    "psychic": {
        "weak_to": ["bug", "ghost", "dark"],
        "strong_against": ["fighting", "poison"],
    },
    "bug": {
        "weak_to": ["fire", "flying", "rock"],
        "strong_against": ["grass", "psychic", "dark"],
    },
    "ghost": {"weak_to": ["ghost", "dark"], "strong_against": ["psychic", "ghost"]},
    "dragon": {"weak_to": ["ice", "dragon", "fairy"], "strong_against": ["dragon"]},
    "steel": {
        "weak_to": ["fire", "fighting", "ground"],
        "strong_against": ["ice", "rock", "fairy"],
    },
    "fairy": {
        "weak_to": ["poison", "steel"],
        "strong_against": ["fighting", "dragon", "dark"],
    },
    "normal": {"weak_to": ["fighting"], "strong_against": []},
    "dark": {"weak_to": ["fighting", "fairy"], "strong_against": ["psychic", "ghost"]},
    "rock": {
        "weak_to": ["water", "grass", "fighting", "ground", "steel"],
        "strong_against": ["fire", "ice", "flying", "bug"],
    },
}


class PokeAPIClient:
    """Wrapper client for PokeAPI with caching."""

    BASE_URL = "https://pokeapi.co/api/v2"
    TIMEOUT = 10

    @lru_cache(maxsize=100)
    def get_pokemon(self, name: str) -> dict:
        """Fetch Pokémon by name (case-insensitive)."""
        response = requests.get(
            f"{self.BASE_URL}/pokemon/{name.lower()}", timeout=self.TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def get_type(self, type_name: str) -> dict:
        """Fetch type by name."""
        response = requests.get(
            f"{self.BASE_URL}/type/{type_name.lower()}", timeout=self.TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def get_move(self, move_name: str) -> dict:
        """Fetch move by name."""
        response = requests.get(
            f"{self.BASE_URL}/move/{move_name.lower()}", timeout=self.TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def get_ability(self, ability_name: str) -> dict:
        """Fetch ability by name."""
        response = requests.get(
            f"{self.BASE_URL}/ability/{ability_name.lower()}", timeout=self.TIMEOUT
        )
        response.raise_for_status()
        return response.json()


def create_api_client() -> "PokeAPIClient | None":
    """Factory to create API client with error handling."""
    try:
        return PokeAPIClient()
    except Exception as e:
        LOG.error(f"Failed to create PokeAPI client: {e}")
        return None


def get_type_advantage(attack_type: str, defend_type: str) -> str:
    """
    Get simplified type advantage explanation for children.
    Returns English keys for translation.
    """
    attack = attack_type.lower()
    defend = defend_type.lower()

    advantages = TYPE_ADVANTAGES.get(attack, {})

    if defend in advantages.get("strong_against", []):
        return "very_effective"
    elif defend in advantages.get("weak_to", []):
        return "not_effective"
    return "neutral"


def format_stat_childfriendly(value: int) -> str:
    """Convert stat to child-friendly tier key."""
    if value >= 120:
        return "very_strong"
    elif value >= 100:
        return "strong"
    elif value >= 80:
        return "normal"
    elif value >= 60:
        return "weak"
    elif value >= 40:
        return "very_weak"
    else:
        return "very_weak"


def format_types_childfriendly(types: list) -> list:
    """Format types list for children (lowercase English)."""
    # Return lowercase English type names
    return [t.lower() for t in types]