"""OVOS Pokémon Battle Assistant Skill.

Child-friendly voice skill for querying Pokémon data and battle predictions.
"""
from typing import Optional

from ovos_bus_client.session import SessionManager
from ovos_utils.log import LOG
from ovos_utils.parse import match_one
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill

from .api_client import (
    PokeAPIClient,
    PokemonPokeAPIError,
    TYPE_ADVANTAGES,
    create_api_client,
    find_next_evolution,
    format_stat_childfriendly,
    format_types_childfriendly,
    get_type_advantage,
)

# OVOS-CONTEXT-1 shared-scope key holding the last Pokémon successfully
# looked up, so a follow-up ("what about its moves?") can resolve without
# repeating the name. This lives on the SESSION (SessionManager.get(message)
# .intent_context), never on the skill instance: the skill is a single
# shared object serving every device/session, so a `self._prev_pokemon`
# attribute would leak one session's last-looked-up Pokémon into every
# other concurrent session's follow-up query.
PREV_POKEMON_CONTEXT = "prev_pokemon"


class PokemonSkill(OVOSSkill):
    """OVOS Skill for Pokémon queries and battles."""

    def __init__(self, *args, **kwargs):
        self.api_client: Optional[PokeAPIClient] = None
        super().__init__(*args, **kwargs)

    # NOTE: no initialize() override here on purpose. The {pokemon_a}/
    # {pokemon_b} slots of battle.intent are constrained by
    # locale/*/intents/pokemon_a.entity and pokemon_b.entity. As of
    # ovos-workshop 9.5.0a1, OVOSSkill auto-discovers and registers every
    # shipped ".entity" file per language during load_lang() - see
    # OVOSSkill._auto_register_entity_files() - so an explicit
    # register_entity_file() call in initialize() is redundant (it would
    # just be a no-op second registration, deduped by resolved file path).

    @property
    def client(self) -> PokeAPIClient:
        """Public accessor — tests / power users can swap with a mock or a
        custom implementation that exposes the same get_pokemon/get_type/
        get_move/get_ability interface."""
        if self.api_client is None:
            self.api_client = create_api_client()
            if self.api_client is None:
                LOG.error("Failed to create PokeAPI client")
        return self.api_client

    # ------------------------------------------------------------------ i18n

    def _phrase(self, key: str, lang: Optional[str] = None) -> str:
        """Look up a localized phrase from phrases.value (key,value CSV).

        Used to translate internal labels — stat tiers, type names,
        battle outcome blurbs — into the active locale's wording. Falls
        back to the bare key if no entry exists.
        """
        try:
            mapping = self.resources.load_named_value_file("phrases")
        except Exception:
            mapping = {}
        return mapping.get(key, key)

    # --------------------------------------------------------------- helpers

    def _load_name_aliases(self) -> dict:
        """Load localized Pokémon-name aliases mapped to PokeAPI slugs."""
        try:
            mapping = self.resources.load_named_value_file("pokemon.name.aliases")
        except Exception:
            mapping = {}
        return {alias.casefold(): canonical for alias, canonical in mapping.items()}

    def _localized_pokemon_name(self, canonical_name: str) -> str:
        """Return the active locale's display name for a PokeAPI slug."""
        try:
            mapping = self.resources.load_named_value_file("pokemon.name.display")
        except Exception:
            mapping = {}
        return mapping.get(canonical_name, canonical_name.replace("-", " ").title())

    def _resolve_pokemon_name(self, name: str) -> str:
        """Map a (possibly misheard) Pokémon name to the closest known one.

        Uses ovos_utils.parse.match_one against the loaded pokemon.voc.
        """
        if not name:
            return name
        name = str(name).strip()
        if not name:
            return name
        aliases = self._load_name_aliases()
        normalized_name = name.casefold()
        if normalized_name in aliases:
            return aliases[normalized_name]
        choices = [n.lower() for n in self.voc_list("pokemon")]
        if not choices:
            return aliases.get(normalized_name, name)
        best, score = match_one(normalized_name, choices)
        return aliases.get(best.casefold(), best) if score >= 0.6 else name

    def _remember_pokemon(self, name: str, message) -> None:
        """Track the last successfully looked-up Pokémon so a follow-up
        query ("what about its moves?") can resolve without repeating the
        name, via the session-scoped ``prev_pokemon`` intent context."""
        session = SessionManager.get(message)
        session.set_intent_context(PREV_POKEMON_CONTEXT, name,
                                    scope="shared", turns_remaining=3)

    def _pokemon_from_message(self, message) -> Optional[str]:
        """Return the ``pokemon`` slot from the message, falling back to
        the last remembered Pokémon (set by ``_remember_pokemon`` on THIS
        message's session) when the slot is absent."""
        slot = message.data.get("pokemon")
        if slot:
            return slot
        session = SessionManager.get(message)
        entry = (session.intent_context or {}).get(PREV_POKEMON_CONTEXT)
        if isinstance(entry, dict) and entry.get("value"):
            return entry["value"]
        return None

    def _format_types(self, types_list) -> str:
        localized = []
        for type_name in types_list:
            type_phrase = self._phrase(f"{type_name}_type")
            if type_phrase == f"{type_name}_type":
                type_phrase = self._phrase(type_name)
            localized.append(type_phrase)
        return self._join_for_speech(localized)

    def _join_for_speech(self, items: list) -> str:
        """Join short localized labels naturally for TTS."""
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        conjunction = self._phrase("list_conjunction")
        if conjunction == "list_conjunction":
            conjunction = {"es": "y", "fr": "et", "it": "e", "pt": "e"}.get(
                self.lang.split("-")[0].lower(), "and"
            )
        return f"{', '.join(items[:-1])} {conjunction} {items[-1]}"

    def _get_type_advantages_for_pokemon(self, pokemon: dict) -> list:
        types = [t["type"]["name"] for t in pokemon["types"]]
        explanation = []
        for t in types:
            if TYPE_ADVANTAGES.get(t, {}).get("strong_against"):
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
        if not explanations:
            return self._phrase("no_specific_advantages")
        return ". ".join(self._phrase(exp) for exp in explanations)

    # ------------------------------------------------------------------ intents

    @intent_handler("GetPokemonInfo.intent")
    def handle_get_pokemon_info(self, message):
        pokemon_name = message.data.get("pokemon")
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return
        if self.client is None:
            self.speak_dialog("error.not.found")
            return

        pokemon_name = self._resolve_pokemon_name(pokemon_name)

        try:
            pokemon = self.client.get_pokemon(pokemon_name)
            stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
            types = [t["type"]["name"] for t in pokemon["types"]]

            self.speak_dialog(
                "pokemon.info",
                {
                    "pokemon_name": self._localized_pokemon_name(pokemon["name"]),
                    "pokedex_number": pokemon["id"],
                    "types": self._format_types(format_types_childfriendly(types)),
                    "attack_desc": self._phrase(
                        format_stat_childfriendly(stats.get("attack", 0))
                    ),
                    "speed_desc": self._phrase(
                        format_stat_childfriendly(stats.get("speed", 0))
                    ),
                },
            )
            self._remember_pokemon(pokemon_name, message)
        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
        except Exception as e:
            LOG.error(f"Failed to get Pokemon info: {e}")
            self.speak_dialog("error.not.found")

    @intent_handler("GetPokemonMoves.intent")
    def handle_get_pokemon_moves(self, message):
        pokemon_name = self._pokemon_from_message(message)
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return
        if self.client is None:
            self.speak_dialog("error.not.found")
            return

        pokemon_name = self._resolve_pokemon_name(pokemon_name)

        try:
            pokemon = self.client.get_pokemon(pokemon_name)
            moves = [
                m["move"]["name"].replace("-", " ").title()
                for m in pokemon["moves"][:5]
            ]
            moves_str = (
                self._join_for_speech(moves)
                if len(moves) > 1
                else (moves[0] if moves else "")
            )
            self.speak_dialog(
                "pokemon.moves",
                {
                    "pokemon_name": self._localized_pokemon_name(pokemon["name"]),
                    "moves": moves_str,
                },
            )
            self._remember_pokemon(pokemon_name, message)
        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
        except Exception as e:
            LOG.error(f"Failed to get Pokemon moves: {e}")
            self.speak_dialog("error.not.found")

    @intent_handler("GetPokemonType.intent")
    def handle_get_pokemon_type(self, message):
        pokemon_name = self._pokemon_from_message(message)
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return
        if self.client is None:
            self.speak_dialog("error.not.found")
            return

        pokemon_name = self._resolve_pokemon_name(pokemon_name)

        try:
            pokemon = self.client.get_pokemon(pokemon_name)
            types = [t["type"]["name"] for t in pokemon["types"]]
            self.speak_dialog(
                "pokemon_type",
                {
                    "pokemon_name": self._localized_pokemon_name(pokemon["name"]),
                    "types": self._format_types(format_types_childfriendly(types)),
                    "explanation": self._format_type_explanation(
                        self._get_type_advantages_for_pokemon(pokemon)
                    ),
                },
            )
            self._remember_pokemon(pokemon_name, message)
        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
        except Exception as e:
            LOG.error(f"Failed to get Pokemon type: {e}")
            self.speak_dialog("error.not.found")

    @intent_handler("GetPokemonEvolution.intent")
    def handle_get_pokemon_evolution(self, message):
        pokemon_name = self._pokemon_from_message(message)
        if not pokemon_name:
            self.speak_dialog("error.no.pokemon")
            return
        if self.client is None:
            self.speak_dialog("error.not.found")
            return

        pokemon_name = self._resolve_pokemon_name(pokemon_name)

        try:
            pokemon = self.client.get_pokemon(pokemon_name)
            chain = self.client.get_evolution_chain(pokemon_name)
            next_name = find_next_evolution(chain, pokemon["name"])
            pokemon_display = self._localized_pokemon_name(pokemon["name"])
            if next_name:
                self.speak_dialog(
                    "evolution",
                    {
                        "pokemon": pokemon_display,
                        "evolution": self._localized_pokemon_name(next_name),
                    },
                )
            else:
                self.speak_dialog("evolution.final", {"pokemon": pokemon_display})
            self._remember_pokemon(pokemon_name, message)
        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
        except Exception as e:
            LOG.error(f"Failed to get Pokemon evolution: {e}")
            self.speak_dialog("error.not.found")

    @intent_handler("battle.intent")
    def handle_battle_comparison(self, message):
        pokemon_a = message.data.get("pokemon_a")
        pokemon_b = message.data.get("pokemon_b")

        if not pokemon_a or not pokemon_b:
            self.speak_dialog("error.battle")
            return
        if self.client is None:
            self.speak_dialog("error.not.found")
            return

        pokemon_a = self._resolve_pokemon_name(pokemon_a)
        pokemon_b = self._resolve_pokemon_name(pokemon_b)

        try:
            pkmn_a = self.client.get_pokemon(pokemon_a)
            pkmn_b = self.client.get_pokemon(pokemon_b)
            stats_a = {s["stat"]["name"]: s["base_stat"] for s in pkmn_a["stats"]}
            stats_b = {s["stat"]["name"]: s["base_stat"] for s in pkmn_b["stats"]}
            types_a = [t["type"]["name"] for t in pkmn_a["types"]]
            types_b = [t["type"]["name"] for t in pkmn_b["types"]]

            type_score_a, type_score_b = self._type_advantage_scores(types_a, types_b)
            score_a = sum(stats_a.values()) + type_score_a * 20
            score_b = sum(stats_b.values()) + type_score_b * 20

            if score_a > score_b + 30:
                winner = self._localized_pokemon_name(pkmn_a["name"])
            elif score_b > score_a + 30:
                winner = self._localized_pokemon_name(pkmn_b["name"])
            else:
                winner = self._phrase("depends_on_moves")

            self.speak_dialog(
                "battle.result",
                {
                    "pokemon_a": self._localized_pokemon_name(pkmn_a["name"]),
                    "pokemon_b": self._localized_pokemon_name(pkmn_b["name"]),
                    "type_a": self._format_types(format_types_childfriendly(types_a)),
                    "type_b": self._format_types(format_types_childfriendly(types_b)),
                    "winner": winner,
                },
            )
        except PokemonPokeAPIError as e:
            LOG.error(f"Pokemon API error: {e}")
            self.speak_dialog("error.not.found")
        except Exception as e:
            LOG.error(f"Failed to compare battle: {e}")
            self.speak_dialog("error.not.found")

    @staticmethod
    def _type_advantage_scores(types_a: list, types_b: list) -> tuple:
        score_a = score_b = 0
        for ta in types_a:
            for tb in types_b:
                r = get_type_advantage(ta, tb)
                if r == "very_effective":
                    score_a += 1
                elif r == "not_effective":
                    score_a -= 1
        for tb in types_b:
            for ta in types_a:
                r = get_type_advantage(tb, ta)
                if r == "very_effective":
                    score_b += 1
                elif r == "not_effective":
                    score_b -= 1
        return score_a, score_b
