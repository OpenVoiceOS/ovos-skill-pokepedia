"""
OVOS Pokémon Battle Assistant Skill
Child-friendly voice skill for querying Pokémon data and battle predictions.
"""

import os
from functools import lru_cache

from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_workshop.intents import IntentBuilder
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill

try:
    import pokepy
except ImportError:
    LOG.warning("pokepy not installed - Pokémon features unavailable")
    pokepy = None


VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_BUILD = 0
VERSION_ALPHA = 0
# END_VERSION_BLOCK


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

    def __init__(self, use_cache: bool = True):
        if pokepy is None:
            raise PokemonPokeAPIError("pokepy library not installed")

        cache = "in_memory" if use_cache else None
        self._client = pokepy.V2Client(cache=cache)

    def get_pokemon(self, name: str):
        """Fetch Pokémon by name (case-insensitive)."""
        return self._client.get_pokemon(name.lower())

    def get_type(self, type_name: str):
        """Fetch type by name."""
        return self._client.get_type(type_name.lower())

    def get_move(self, move_name: str):
        """Fetch move by name."""
        return self._client.get_move(move_name.lower())

    def get_ability(self, ability_name: str):
        """Fetch ability by name."""
        return self._client.get_ability(ability_name.lower())


def create_api_client() -> "PokeAPIClient | None":
    """Factory to create API client with error handling."""
    if pokepy is None:
        return None
    try:
        return PokeAPIClient(use_cache=True)
    except Exception as e:
        LOG.error(f"Failed to create PokeAPI client: {e}")
        return None


def get_type_advantage(attack_type: str, defend_type: str) -> str:
    """
    Get simplified type advantage explanation for children.
    Returns Italian explanation string.
    """
    attack = attack_type.lower()
    defend = defend_type.lower()

    advantages = TYPE_ADVANTAGES.get(attack, {})

    if defend in advantages.get("strong_against", []):
        return "molto efficace"
    elif defend in advantages.get("weak_to", []):
        return "non molto efficace"
    return "neutro"


def format_stat_childfriendly(stat_name: str, value: int) -> str:
    """Convert stat to child-friendly Italian description."""
    stat_map = {
        "hp": "punti vita",
        "attack": "attacco",
        "defense": "difesa",
        "special-attack": "attacco speciale",
        "special-defense": "difesa speciale",
        "speed": "velocità",
    }

    name = stat_map.get(stat_name, stat_name)

    if value >= 120:
        return f"un {name} fortissimo"
    elif value >= 100:
        return f"un {name} molto forte"
    elif value >= 80:
        return f"un buon {name}"
    elif value >= 60:
        return f"un {name} normale"
    elif value >= 40:
        return f"un {name} debole"
    else:
        return f"un {name} molto debole"


def format_types_childfriendly(types: list) -> str:
    """Format types list for children in Italian."""
    type_map = {
        "fire": "Fuoco",
        "water": "Acqua",
        "grass": "Erba",
        "electric": "Elettrico",
        "ice": "Ghiaccio",
        "fighting": "Lotta",
        "poison": "Veleno",
        "ground": "Terra",
        "flying": "Volante",
        "psychic": "Psico",
        "bug": "Coleottero",
        "ghost": "Spettro",
        "dragon": "Drago",
        "steel": "Acciaio",
        "fairy": "Folletto",
        "normal": "Normale",
        "dark": "Buio",
        "rock": "Roccia",
    }

    italian_types = [type_map.get(t, t.capitalize()) for t in types]

    if len(italian_types) == 1:
        return italian_types[0]
    return f"{italian_types[0]} e {italian_types[1]}"


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
        LOG.info("PokemonSkill initialized")

    @intent_handler(
        IntentBuilder("GetPokemonInfo").require("TellMeKeyword").require("PokemonName")
    )
    def handle_get_pokemon_info(self, message):
        pokemon_name = message.data.get("PokemonName")
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            stats = {s.stat.name: s.base_stat for s in pokemon.stats}
            types = [t.type.name for t in pokemon.types]
            abilities = [a.ability.name for a in pokemon.abilities]

            attack_desc = format_stat_childfriendly("attack", stats.get("attack", 0))
            speed_desc = format_stat_childfriendly("speed", stats.get("speed", 0))
            types_desc = format_types_childfriendly(types)

            self.speak_dialog(
                "pokemon.info",
                {
                    "pokemon_name": pokemon.name.capitalize(),
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

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            moves = [m.move.name.replace("-", " ").title() for m in pokemon.moves[:5]]
            moves_str = (
                ", ".join(moves[:-1]) + " e " + moves[-1]
                if len(moves) > 1
                else moves[0]
            )

            self.speak_dialog(
                "pokemon.moves",
                {
                    "pokemon_name": pokemon.name.capitalize(),
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

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            types = [t.type.name for t in pokemon.types]
            types_desc = format_types_childfriendly(types)

            explanation = []
            for t in types:
                advantages = TYPE_ADVANTAGES.get(t, {})
                if advantages.get("strong_against"):
                    type_map = {
                        "fire": "Erba",
                        "water": "Fuoco",
                        "grass": "Acqua",
                        "electric": "Acqua",
                        "ice": "Erba",
                        "fighting": "Normale",
                    }
                    strong = type_map.get(t, t.capitalize())
                    explanation.append(f"forte contro {strong}")

            explanation_str = (
                ". ".join(explanation) if explanation else "Non ha vantaggi specifici"
            )

            self.speak_dialog(
                "pokemon.type",
                {
                    "pokemon_name": pokemon.name.capitalize(),
                    "types": types_desc,
                    "explanation": explanation_str,
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

        try:
            pkmn_a = self.api_client.get_pokemon(pokemon_a)
            pkmn_b = self.api_client.get_pokemon(pokemon_b)

            stats_a = {s.stat.name: s.base_stat for s in pkmn_a.stats}
            stats_b = {s.stat.name: s.base_stat for s in pkmn_b.stats}

            types_a = [t.type.name for t in pkmn_a.types]
            types_b = [t.type.name for t in pkmn_b.types]

            total_a = sum(stats_a.values())
            total_b = sum(stats_b.values())

            type_advantage_a = 0
            type_advantage_b = 0

            for ta in types_a:
                for tb in types_b:
                    result = get_type_advantage(ta, tb)
                    if result == "molto efficace":
                        type_advantage_a += 1
                    elif result == "non molto efficace":
                        type_advantage_a -= 1

            for tb in types_b:
                for ta in types_a:
                    result = get_type_advantage(tb, ta)
                    if result == "molto efficace":
                        type_advantage_b += 1
                    elif result == "non molto efficace":
                        type_advantage_b -= 1

            score_a = total_a + (type_advantage_a * 20)
            score_b = total_b + (type_advantage_b * 20)

            if score_a > score_b + 30:
                winner = pkmn_a.name.capitalize()
            elif score_b > score_a + 30:
                winner = pkmn_b.name.capitalize()
            else:
                winner = "dipende dal tipo di mosse"

            types_a_desc = format_types_childfriendly(types_a)
            types_b_desc = format_types_childfriendly(types_b)

            self.speak_dialog(
                "battle.result",
                {
                    "pokemon_a": pkmn_a.name.capitalize(),
                    "pokemon_b": pkmn_b.name.capitalize(),
                    "type_a": types_a_desc,
                    "type_b": types_b_desc,
                    "winner": winner,
                },
            )

        except Exception as e:
            LOG.error(f"Failed to compare battle: {e}")
            self.speak_dialog("error.not.found")
