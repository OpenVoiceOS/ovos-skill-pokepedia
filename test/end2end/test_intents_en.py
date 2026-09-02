"""Intent-routing coverage for en-US.

One canonical utterance per intent family: the Padatious
``GetPokemonInfo`` and ``GetPokemonType`` file intents, and the Padatious
``battle.intent``. Each asserts the intent routed and the skill spoke — a
drift-immune subset, never an ordered message sequence.
"""
from unittest import TestCase

from ._helpers import SKILL_ID, IntentRoutingMixin, _PADATIOUS_PIPELINE


class TestEnIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_info_routes_through_padatious(self):
        self._assert_intent(
            "tell me about the pokemon pikachu", "GetPokemonInfo", padatious=True
        )

    def test_type_routes_through_padatious(self):
        self._assert_intent(
            "what type is the pokemon charizard", "GetPokemonType", padatious=True
        )

    def test_battle_routes_through_padatious(self):
        self._assert_routes(
            "who wins pikachu or bulbasaur", "battle.intent", padatious=True
        )

    def test_battle_speaks_after_padatious_match(self):
        self._assert_intent(
            "who wins pikachu or bulbasaur", "battle.intent", padatious=True
        )

    def test_evolution_routes_through_padatious(self):
        self._assert_intent(
            "what does charmander evolve into",
            "GetPokemonEvolution",
            padatious=True,
        )

    def test_moves_context_fallback_after_info_lookup(self):
        # Both turns share ONE session id: the "prev_pokemon" context lives
        # on the session (OVOS-CONTEXT-1), not on the skill instance, so a
        # follow-up only resolves within the SAME conversation.
        session_id = "pokepedia-en-US-moves-context-fallback"
        # First establish "pikachu" as the last-discussed pokemon...
        self._assert_intent(
            "tell me about the pokemon pikachu", "GetPokemonInfo",
            padatious=True, session_id=session_id,
        )
        # ...then a follow-up with no {pokemon} slot resolves via context.
        self._assert_intent(
            "what about its moves", "GetPokemonMoves",
            padatious=True, session_id=session_id,
        )

    def test_moves_without_context_still_routes_but_cannot_resolve_pokemon(self):
        # A brand-new session has never looked anything up: the intent still
        # matches (context-free phrasing is valid padatious training data)
        # but the skill has nothing to fall back on and must speak the "no
        # pokemon" error rather than crash.
        types = self._assert_routes(
            "what type is it", "GetPokemonType", padatious=True,
            session_id="pokepedia-en-US-moves-no-context",
        )
        self.assertTrue(set(types) & {"speak", "ovos.utterance.speak"})

    def test_prev_pokemon_context_is_session_isolated(self):
        # Reviewer repro (issue #32 follow-up): device A looks up a Pokémon,
        # device B (a different session) asks a context-only follow-up and
        # must NOT resolve to device A's Pokémon.
        self._assert_intent(
            "tell me about the pokemon charmander", "GetPokemonInfo",
            padatious=True, session_id="pokepedia-en-US-device-a",
        )
        spoken = self._spoken_texts(
            "what about its moves", _PADATIOUS_PIPELINE,
            session_id="pokepedia-en-US-device-b",
        )
        self.assertTrue(spoken, "device B never spoke at all")
        self.assertFalse(
            any("charmander" in u.lower() for u in spoken),
            f"device B resolved device A's remembered Pokémon: {spoken}",
        )
