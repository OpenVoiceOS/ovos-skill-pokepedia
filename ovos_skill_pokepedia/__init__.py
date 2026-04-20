"""
OVOS Pokémon Battle Assistant Skill
Child-friendly voice skill for querying Pokémon data and battle predictions.
"""

import requests
from functools import lru_cache

from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_workshop.intents import IntentBuilder
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill

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


class PokemonPokeAPIError(Exception):
    """Error when fetching Pokémon data from API fails."""

    pass


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


class PokemonSkill(OVOSSkill):
    """OVOS Skill for Pokémon queries and battles."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = None

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(
            internet_before_load=True,
            network_before_load=False,
            gui_before_load=False,
            requires_internet=True,
            requires_network=False,
            requires_gui=False,
            no_internet_fallback=False,
            no_network_fallback=True,
            no_gui_fallback=True,
        )

    def initialize(self):
        self.api_client = create_api_client()
        if self.api_client is None:
            LOG.error("Failed to create PokeAPI client")
        LOG.info("PokemonSkill initialized")

    @intent_handler(
        IntentBuilder("GetPokemonInfo").require("TellMeKeyword").require("PokemonName")
    )
    def handle_get_pokemon_info(self, message):
        pokemon_name = message.data.get("PokemonName")
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return

        if self.api_client is None:
            self.speak_dialog("error.not.found")
            return

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
            types = [t["type"]["name"] for t in pokemon["types"]]

            attack_tier = format_stat_childfriendly(stats.get("attack", 0))
            speed_tier = format_stat_childfriendly(stats.get("speed", 0))
            types_list = format_types_childfriendly(types)

            # Translate types
            types_desc = " and ".join(self._translate(t) for t in types_list)
            # Translate stat tiers
            attack_desc = self._translate(attack_tier)
            speed_desc = self._translate(speed_tier)

            self.speak_dialog(
                "pokemon.info",
                {
                    "pokemon_name": pokemon["name"].capitalize(),
                    "pokedex_number": pokemon["id"],
                    "types": types_desc,
                    "attack_desc": attack_desc,
                    "speed_desc": speed_desc,
                },
            )

        except Exception as e:
            LOG.error(f"Failed to get Pokemon info: {e}")
            self.speak_dialog("error.not.found")

    @intent_handler(
        IntentBuilder("GetPokemonMoves").require("MovesKeyword").require("PokemonName")
    )
    def handle_get_pokemon_moves(self, message):
        pokemon_name = message.data.get("PokemonName")
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return

        if self.api_client is None:
            self.speak_dialog("error.not.found")
            return

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            moves = [
                m["move"]["name"].replace("-", " ").title()
                for m in pokemon["moves"][:5]
            ]
            moves_str = (
                ", ".join(moves[:-1]) + " and " + moves[-1]
                if len(moves) > 1
                else moves[0]
            )

            self.speak_dialog(
                "pokemon.moves",
                {
                    "pokemon_name": pokemon["name"].capitalize(),
                    "moves": moves_str,
                },
            )

        except Exception as e:
            LOG.error(f"Failed to get Pokemon moves: {e}")
            self.speak_dialog("error.not.found")

    @intent_handler(
        IntentBuilder("GetPokemonType").require("TypeKeyword").require("PokemonName")
    )
    def handle_get_pokemon_type(self, message):
        pokemon_name = message.data.get("PokemonName")
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return

        if self.api_client is None:
            self.speak_dialog("error.not.found")
            return

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            types = [t["type"]["name"] for t in pokemon["types"]]
            types_list = format_types_childfriendly(types)

            explanation = []
            for t in types:
                advantages = TYPE_ADVANTAGES.get(t, {})
                if advantages.get("strong_against"):
                    # Use mapping for translation keys (instead of hardcoded Italian)
                    type_map = {
                        "fire": "grass",
                        "water": "fire",
                        "grass": "water",
                        "electric": "water",
                        "ice": "grass",
                        "fighting": "normal",
                    }
                    strong = type_map.get(t, t)
                    explanation.append(f"strong_against_{strong}")

            # Translate types
            types_desc = " and ".join(self._translate(t) for t in types_list)
            # Translate explanation keys
            explanation_translated = (
                ". ".join(self._translate(exp) for exp in explanation)
                if explanation
                else self._translate("no_specific_advantages")
            )

            self.speak_dialog(
                "pokemon.type",
                {
                    "pokemon_name": pokemon["name"].capitalize(),
                    "types": types_desc,
                    "explanation": explanation_translated,
                },
            )

        except Exception as e:
            LOG.error(f"Failed to get Pokemon type: {e}")
            self.speak_dialog("error.not.found")

    @intent_handler(
        IntentBuilder("BattleComparison")
        .require("BattleKeyword")
        .require("PokemonA")
        .one_of("PokemonA", "PokemonB")
    )
    def handle_battle_comparison(self, message):
        pokemon_a = message.data.get("PokemonA")
        pokemon_b = message.data.get("PokemonB")

        if not pokemon_a or not pokemon_b:
            self.speak_dialog("error.battle")
            return

        if self.api_client is None:
            self.speak_dialog("error.not.found")
            return

        try:
            pkmn_a = self.api_client.get_pokemon(pokemon_a)
            pkmn_b = self.api_client.get_pokemon(pokemon_b)

            stats_a = {s["stat"]["name"]: s["base_stat"] for s in pkmn_a["stats"]}
            stats_b = {s["stat"]["name"]: s["base_stat"] for s in pkmn_b["stats"]}

            types_a = [t["type"]["name"] for t in pkmn_a["types"]]
            types_b = [t["type"]["name"] for t in pkmn_b["types"]]

            total_a = sum(stats_a.values())
            total_b = sum(stats_b.values())

            type_advantage_a = 0
            type_advantage_b = 0

            for ta in types_a:
                for tb in types_b:
                    result = get_type_advantage(ta, tb)
                    if result == "very_effective":
                        type_advantage_a += 1
                    elif result == "not_effective":
                        type_advantage_a -= 1

            for tb in types_b:
                for ta in types_a:
                    result = get_type_advantage(tb, ta)
                    if result == "very_effective":
                        type_advantage_b += 1
                    elif result == "not_effective":
                        type_advantage_b -= 1

            score_a = total_a + (type_advantage_a * 20)
            score_b = total_b + (type_advantage_b * 20)

            if score_a > score_b + 30:
                winner = pkmn_a["name"].capitalize()
            elif score_b > score_a + 30:
                winner = pkmn_b["name"].capitalize()
            else:
                winner = self._translate("depends_on_moves")

            types_a_list = format_types_childfriendly(types_a)
            types_b_list = format_types_childfriendly(types_b)

            # Translate types
            types_a_desc = " and ".join(self._translate(t) for t in types_a_list)
            types_b_desc = " and ".join(self._translate(t) for t in types_b_list)

            self.speak_dialog(
                "battle.result",
                {
                    "pokemon_a": pkmn_a["name"].capitalize(),
                    "pokemon_b": pkmn_b["name"].capitalize(),
                    "type_a": types_a_desc,
                    "type_b": types_b_desc,
                    "winner": winner,
                },
            )

        except Exception as e:
            LOG.error(f"Failed to compare battle: {e}")
            self.speak_dialog("error.not.found")
