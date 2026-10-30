"""Unit tests for helper modules of the OVOS Pokémon Battle Assistant skill.

End-to-end intent-routing coverage lives in ``test/end2end/`` and exercises
the skill via ovoscope's MiniCroft — these unit tests cover pure helpers
(type advantages, child-friendly formatting, fuzzy matcher, API client
constructor) where a live bus is unnecessary.
"""
import json
import uuid
from pathlib import Path
from unittest import mock

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import SessionManager
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


class TestFindNextEvolution:
    CHAIN = {
        "species": {"name": "charmander"},
        "evolves_to": [
            {
                "species": {"name": "charmeleon"},
                "evolves_to": [
                    {"species": {"name": "charizard"}, "evolves_to": []}
                ],
            }
        ],
    }

    def test_finds_middle_stage(self):
        from ovos_skill_pokepedia.api_client import find_next_evolution
        assert find_next_evolution(self.CHAIN, "charmander") == "charmeleon"

    def test_finds_final_step_from_middle(self):
        from ovos_skill_pokepedia.api_client import find_next_evolution
        assert find_next_evolution(self.CHAIN, "charmeleon") == "charizard"

    def test_final_stage_returns_none(self):
        from ovos_skill_pokepedia.api_client import find_next_evolution
        assert find_next_evolution(self.CHAIN, "charizard") is None

    def test_name_not_in_chain_returns_none(self):
        from ovos_skill_pokepedia.api_client import find_next_evolution
        assert find_next_evolution(self.CHAIN, "pikachu") is None

    def test_case_insensitive(self):
        from ovos_skill_pokepedia.api_client import find_next_evolution
        assert find_next_evolution(self.CHAIN, "CHARMANDER") == "charmeleon"


class _FakeEvolutionClient:
    def __init__(self, pokemon, chain):
        self._pokemon = pokemon
        self._chain = chain
        self.asked = []

    def get_pokemon(self, name):
        self.asked.append(name)
        return self._pokemon

    def get_evolution_chain(self, name):
        self.asked.append(name)
        return self._chain


class _StrictEvolutionClient(_FakeEvolutionClient):
    """A client that answers only for the Pokemon it knows.

    The permissive fake above returns its one payload whatever name it is
    handed, so a handler that asks for "it" still gets Pikachu back and a
    test on the spoken dialog cannot see the defect: removing the slot
    exclusion left such a test green. The real API 404s, and so does this.
    """

    def __init__(self, known, pokemon, chain):
        super().__init__(pokemon, chain)
        self._known = known

    def get_pokemon(self, name):
        self.asked.append(name)
        if name != self._known:
            return None
        return self._pokemon

    def get_evolution_chain(self, name):
        self.asked.append(name)
        if name != self._known:
            return None
        return self._chain


class TestEvolutionIntentAndContextFallback:
    """Covers get_pokemon_evolution and the prev_pokemon context fallback on
    get_pokemon_moves/get_pokemon_type/get_pokemon_evolution (issue #32), plus the
    session isolation the context must respect: the remembered Pokémon lives
    on the SESSION (OVOS-CONTEXT-1 ``intent_context``), never on the skill
    instance, since one shared skill instance serves every device/session.

    This harness has no real bus (see the module docstring: pure-helper
    coverage lives here, real dispatch lives in ``test/end2end/``), so there
    is no ``ovos.utterance.speak``/``mycroft.skill.handler.complete`` wire to
    listen on. The next best thing to reading the orchestrator's private
    ``SessionManager.sessions`` registry is capturing the exact ``Session``
    object the handler itself asked for and mutated, via a spy on the same
    public ``SessionManager.get(message)`` call the skill code makes — never
    the registry it is backed by. That captured session's serialized form is
    then explicitly re-declared as the next turn's message context, exactly
    as a real client would re-declare a session id."""

    @staticmethod
    def _make_skill(client=None):
        from ovos_skill_pokepedia import PokemonSkill

        class Harness:
            _name_table = PokemonSkill._name_table
            _load_name_aliases = PokemonSkill._load_name_aliases
            _resolve_pokemon_name = PokemonSkill._resolve_pokemon_name
            _localized_pokemon_name = PokemonSkill._localized_pokemon_name
            _remember_pokemon = PokemonSkill._remember_pokemon
            _pokemon_from_message = PokemonSkill._pokemon_from_message
            _format_types = PokemonSkill._format_types
            _join_for_speech = PokemonSkill._join_for_speech
            _phrase = PokemonSkill._phrase
            _format_type_explanation = PokemonSkill._format_type_explanation
            _get_type_advantages_for_pokemon = (
                PokemonSkill._get_type_advantages_for_pokemon
            )
            handle_get_pokemon_evolution = PokemonSkill.handle_get_pokemon_evolution
            handle_get_pokemon_moves = PokemonSkill.handle_get_pokemon_moves
            handle_get_pokemon_type = PokemonSkill.handle_get_pokemon_type

            def __init__(self):
                self.api_client = client
                self.spoken = []
                self.dialog_renderer = SkillResources(
                    str(PACKAGE_DIR), "en-US"
                ).dialog_renderer
                self.lang = "en-US"

            @property
            def client(self):
                return self.api_client

            def voc_list(self, name):
                return []

            def speak_dialog(self, key, data=None):
                self.spoken.append((key, data or {}))

        return Harness()

    @staticmethod
    def _msg(session=None, data=None):
        """Build a Message declaring ``session`` (a serialized session dict
        captured from a previous turn), or a fresh client-chosen session id
        when omitted - never one pulled from the orchestrator's registry."""
        session = session or {"session_id": f"poke-{uuid.uuid4()}"}
        return Message("intent", data or {}, {"session": session})

    @staticmethod
    def _call(handler, message):
        """Call ``handler(message)`` and capture the ``Session`` object the
        handler itself obtained via ``SessionManager.get(message)`` - the
        same call the skill code makes internally - by spying on that public
        entry point rather than reading the registry after the fact.

        Returns the session's serialized form for re-declaring on the next
        turn.
        """
        captured = {}
        real_get = SessionManager.get

        def _spy_get(msg=None):
            session = real_get(msg)
            captured["session"] = session
            return session

        with mock.patch("ovos_skill_pokepedia.SessionManager.get", side_effect=_spy_get):
            handler(message)
        return captured["session"].serialize() if captured.get("session") else None

    def test_evolution_speaks_next_stage(self):
        chain = {
            "species": {"name": "charmander"},
            "evolves_to": [
                {"species": {"name": "charmeleon"}, "evolves_to": []}
            ],
        }
        skill = self._make_skill(
            _FakeEvolutionClient({"name": "charmander"}, chain)
        )
        session = self._call(
            skill.handle_get_pokemon_evolution,
            self._msg(data={"pokemon": "charmander"}),
        )

        assert skill.spoken == [
            ("evolution", {"pokemon": "Charmander", "evolution": "Charmeleon"})
        ]
        entry = session["intent_context"].get("prev_pokemon")
        assert entry == {"value": "charmander", "turns_remaining": 3}

    def test_evolution_speaks_final_stage_dialog(self):
        chain = {"species": {"name": "charizard"}, "evolves_to": []}
        skill = self._make_skill(
            _FakeEvolutionClient({"name": "charizard"}, chain)
        )
        skill.handle_get_pokemon_evolution(
            self._msg(data={"pokemon": "charizard"})
        )

        assert skill.spoken == [("evolution_final", {"pokemon": "Charizard"})]

    def test_evolution_without_pokemon_or_context_speaks_error(self):
        skill = self._make_skill(_FakeEvolutionClient({}, {}))
        skill.handle_get_pokemon_evolution(self._msg())

        assert skill.spoken == [("error_no_pokemon", {})]

    def test_moves_falls_back_to_prev_pokemon_context(self):
        pokemon = {
            "name": "pikachu",
            "moves": [{"move": {"name": "thunderbolt"}}],
        }
        skill = self._make_skill(_FakeEvolutionClient(pokemon, {}))
        session = self._call(
            lambda m: skill._remember_pokemon("pikachu", m), self._msg())

        skill.handle_get_pokemon_moves(self._msg(session=session))

        assert skill.spoken == [
            ("moves", {"pokemon_name": "Pikachu", "moves": "Thunderbolt"})
        ]

    def test_moves_without_pokemon_or_context_speaks_error(self):
        skill = self._make_skill(_FakeEvolutionClient({}, {}))

        skill.handle_get_pokemon_moves(self._msg())

        assert skill.spoken == [("error_no_pokemon", {})]

    def test_explicit_pokemon_slot_wins_over_stale_context(self):
        pokemon = {
            "name": "bulbasaur",
            "moves": [{"move": {"name": "vine-whip"}}],
        }
        skill = self._make_skill(_FakeEvolutionClient(pokemon, {}))
        session = self._call(
            lambda m: skill._remember_pokemon("charmander", m), self._msg())

        session = self._call(
            skill.handle_get_pokemon_moves,
            self._msg(session=session, data={"pokemon": "bulbasaur"}),
        )

        assert skill.spoken == [
            ("moves", {"pokemon_name": "Bulbasaur", "moves": "Vine Whip"})
        ]
        assert session["intent_context"].get("prev_pokemon") == {
            "value": "bulbasaur", "turns_remaining": 3,
        }

    def test_a_real_name_still_wins_over_the_context(self):
        """A name in the slot wins over the remembered Pokemon."""
        pokemon = {
            "name": "bulbasaur",
            "moves": [{"move": {"name": "vine-whip"}}],
        }
        client = _StrictEvolutionClient("bulbasaur", pokemon, {})
        skill = self._make_skill(client)
        session = self._call(
            lambda m: skill._remember_pokemon("charmander", m), self._msg())

        skill.handle_get_pokemon_moves(
            self._msg(session=session, data={"pokemon": "bulbasaur"}))

        assert client.asked == ["bulbasaur"], (
            f"the name lost to the remembered Pokemon: {client.asked!r}")
        assert skill.spoken == [
            ("moves", {"pokemon_name": "Bulbasaur", "moves": "Vine Whip"})
        ]

    def test_prev_pokemon_context_is_session_isolated(self):
        """Reviewer repro (issue #32 follow-up): two DIFFERENT sessions must
        never share a remembered Pokémon. Session A looks up Charmander;
        session B's "what about its moves" (no {pokemon} slot) must NOT
        resolve to Charmander, since B never looked anything up."""
        chain = {"species": {"name": "charmander"}, "evolves_to": []}
        skill = self._make_skill(_FakeEvolutionClient({"name": "charmander"}, chain))

        skill.handle_get_pokemon_evolution(self._msg(data={"pokemon": "charmander"}))
        assert skill.spoken[-1] == ("evolution_final", {"pokemon": "Charmander"})

        skill.spoken.clear()
        skill.handle_get_pokemon_moves(self._msg())

        assert skill.spoken == [("error_no_pokemon", {})], (
            "device B resolved device A's remembered Pokémon "
            f"instead of erroring: {skill.spoken}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
