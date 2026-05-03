"""
OVOS Pokémon Battle Assistant Skill
Child-friendly voice skill for querying Pokémon data and battle predictions.
"""

from .api_client import (
    PokemonPokeAPIError,
    PokeAPIClient,
    create_api_client,
    get_type_advantage,
    format_stat_childfriendly,
    format_types_childfriendly,
    TYPE_ADVANTAGES,
)

from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_workshop.intents import IntentBuilder
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill


class PokemonSkill(OVOSSkill):
    """OVOS Skill for Pokémon queries and battles."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client: PokeAPIClient = None
        self.fuzzy_matcher = None

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

    @property
    def client(self) -> PokeAPIClient:
        """Public accessor for the API client.

        Allows users to replace the client with a custom implementation:
            skill.client = CustomPokemonClient()

        The client must implement:
            - get_pokemon(name: str) -> dict
            - get_type(type_name: str) -> dict
            - get_move(move_name: str) -> dict
            - get_ability(ability_name: str) -> dict
        """
        return self.api_client

    def initialize(self):
        self.api_client = create_api_client()
        if self.api_client is None:
            LOG.error("Failed to create PokeAPI client")

        # Initialize fuzzy matcher
        try:
            from .fuzzy_matcher import PokemonFuzzyMatcher
            self.fuzzy_matcher = PokemonFuzzyMatcher()
        except Exception as e:
            LOG.warning(f"Failed to initialize fuzzy matcher: {e}")
            self.fuzzy_matcher = None

        LOG.info("PokemonSkill initialized")

    def _resolve_pokemon_name(self, name: str) -> str:
        """Resolve potentially misspelled Pokémon name using fuzzy matching."""
        if not self.fuzzy_matcher or not name:
            return name
        try:
            matched, confidence = self.fuzzy_matcher.match(name)
            if confidence >= 0.6:
                return matched
        except Exception:
            pass
        return name

    def _get_type_advantages_for_pokemon(self, pokemon: dict) -> list:
        """Extract type advantages for a Pokémon's types."""
        types = [t["type"]["name"] for t in pokemon["types"]]
        explanation = []
        for t in types:
            advantages = TYPE_ADVANTAGES.get(t, {})
            if advantages.get("strong_against"):
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
        return explanation

    def _format_type_explanation(self, explanations: list) -> str:
        """Format type explanation for TTS output."""
        if not explanations:
            return self._translate("no_specific_advantages")
        return ". ".join(self._translate(exp) for exp in explanations)

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

        # Use fuzzy matching to resolve potentially misspelled names
        pokemon_name = self._resolve_pokemon_name(pokemon_name)

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
            types = [t["type"]["name"] for t in pokemon["types"]]

            attack_tier = format_stat_childfriendly(stats.get("attack", 0))
            speed_tier = format_stat_childfriendly(stats.get("speed", 0))
            types_list = format_types_childfriendly(types)

            types_desc = " and ".join(self._translate(t) for t in types_list)
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

        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
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

        pokemon_name = self._resolve_pokemon_name(pokemon_name)

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

        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
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

        pokemon_name = self._resolve_pokemon_name(pokemon_name)

        try:
            pokemon = self.api_client.get_pokemon(pokemon_name)

            types = [t["type"]["name"] for t in pokemon["types"]]
            types_list = format_types_childfriendly(types)

            explanation = self._get_type_advantages_for_pokemon(pokemon)
            types_desc = " and ".join(self._translate(t) for t in types_list)
            explanation_translated = self._format_type_explanation(explanation)

            self.speak_dialog(
                "pokemon.type",
                {
                    "pokemon_name": pokemon["name"].capitalize(),
                    "types": types_desc,
                    "explanation": explanation_translated,
                },
            )

        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
        except Exception as e:
            LOG.error(f"Failed to get Pokemon type: {e}")
            self.speak_dialog("error.not.found")

    def _fetch_battle_pokemon(self, name: str) -> dict:
        """Fetch Pokémon data for battle comparison."""
        return self.api_client.get_pokemon(name)

    def _calculate_type_advantage_score(self, types_a: list, types_b: list) -> tuple:
        """Calculate type advantage scores for both Pokémon."""
        score_a = 0
        score_b = 0

        for ta in types_a:
            for tb in types_b:
                result = get_type_advantage(ta, tb)
                if result == "very_effective":
                    score_a += 1
                elif result == "not_effective":
                    score_a -= 1

        for tb in types_b:
            for ta in types_a:
                result = get_type_advantage(tb, ta)
                if result == "very_effective":
                    score_b += 1
                elif result == "not_effective":
                    score_b -= 1

        return score_a, score_b

    def _calculate_battle_score(self, stats: dict, type_score: int) -> int:
        """Calculate total battle score from stats and type advantage."""
        total = sum(stats.values())
        return total + (type_score * 20)

    def _determine_winner(self, score_a: int, score_b: int, name_a: str, name_b: str) -> str:
        """Determine battle winner based on scores."""
        if score_a > score_b + 30:
            return name_a.capitalize()
        elif score_b > score_a + 30:
            return name_b.capitalize()
        return self._translate("depends_on_moves")

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

        # Use fuzzy matching for both Pokémon
        pokemon_a = self._resolve_pokemon_name(pokemon_a)
        pokemon_b = self._resolve_pokemon_name(pokemon_b)

        try:
            pkmn_a = self._fetch_battle_pokemon(pokemon_a)
            pkmn_b = self._fetch_battle_pokemon(pokemon_b)

            stats_a = {s["stat"]["name"]: s["base_stat"] for s in pkmn_a["stats"]}
            stats_b = {s["stat"]["name"]: s["base_stat"] for s in pkmn_b["stats"]}

            types_a = [t["type"]["name"] for t in pkmn_a["types"]]
            types_b = [t["type"]["name"] for t in pkmn_b["types"]]

            type_score_a, type_score_b = self._calculate_type_advantage_score(
                types_a, types_b
            )

            score_a = self._calculate_battle_score(stats_a, type_score_a)
            score_b = self._calculate_battle_score(stats_b, type_score_b)

            winner = self._determine_winner(
                score_a, score_b, pkmn_a["name"], pkmn_b["name"]
            )

            types_a_list = format_types_childfriendly(types_a)
            types_b_list = format_types_childfriendly(types_b)

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

        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
        except Exception as e:
            LOG.error(f"Failed to compare battle: {e}")
            self.speak_dialog("error.not.found")