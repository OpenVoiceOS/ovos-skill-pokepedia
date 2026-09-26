"""Intent-routing coverage for en-US.

One canonical utterance per intent family: the Padatious
``get_pokemon_info`` and ``get_pokemon_type`` file intents, and the Padatious
``battle.intent``. Each asserts the intent routed and the skill spoke — a
drift-immune subset, never an ordered message sequence.
"""
from unittest import TestCase

from ._helpers import (SKILL_ID, IntentRoutingMixin, _PADATIOUS_PIPELINE,
                        _intent_candidates, _session_after, _spoken, _SPOKE)


class TestEnIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_info_routes_through_padatious(self):
        self._assert_intent(
            "tell me about the pokemon pikachu", "get_pokemon_info", padatious=True
        )

    def test_type_routes_through_padatious(self):
        self._assert_intent(
            "what type is the pokemon charizard", "get_pokemon_type", padatious=True
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
            "get_pokemon_evolution",
            padatious=True,
        )

    def test_moves_context_fallback_after_info_lookup(self):
        """The follow-up must answer ABOUT pikachu, named by nothing but the
        context the first turn left behind.

        Both turns share one session OBJECT, carried forward with
        `_session_after`. Sharing only the session id is not enough: a named
        session keeps no state in SessionManager, so the second turn would
        start from an empty context and the skill would speak
        `error_no_pokemon` while the test still passed, because routing
        happened and something was spoken.

        The assertion is therefore on the answer, not on the fact of an
        answer. Delete the fallback branch in `_pokemon_from_message` and this
        test fails.
        """
        session = self._new_session(_PADATIOUS_PIPELINE,
                                    "pokepedia-en-US-moves-context-fallback")

        first = self._capture_messages("tell me about the pokemon pikachu",
                                        _PADATIOUS_PIPELINE, session=session)
        types = [m.msg_type for m in first]
        self.assertTrue(
            any(t in _intent_candidates("get_pokemon_info") for t in types),
            f"turn 1 did not route to get_pokemon_info (captured: {types})",
        )
        self.assertTrue(
            any("pikachu" in u.lower() for u in _spoken(first)),
            f"turn 1 never named pikachu: {_spoken(first)}",
        )

        session = _session_after(first, session)
        self.assertEqual(
            (session.intent_context or {}).get("prev_pokemon", {}).get("value"),
            "pikachu",
            "turn 1 left no prev_pokemon on the session it handed back, so no "
            f"follow-up can resolve: {session.intent_context!r}",
        )

        second = self._capture_messages("what about its moves",
                                         _PADATIOUS_PIPELINE, session=session)
        types = [m.msg_type for m in second]
        self.assertTrue(
            any(t in _intent_candidates("get_pokemon_moves") for t in types),
            f"turn 2 did not route to get_pokemon_moves (captured: {types})",
        )
        spoken = _spoken(second)
        self.assertTrue(spoken, f"turn 2 never spoke (captured: {types})")
        self.assertTrue(
            any("pikachu" in u.lower() for u in spoken),
            "turn 2 did not resolve pikachu from context; the skill answered "
            f"{spoken!r}",
        )

    def test_moves_without_context_still_routes_but_cannot_resolve_pokemon(self):
        # A brand-new session has never looked anything up: the intent still
        # matches (context-free phrasing is valid padatious training data)
        # but the skill has nothing to fall back on and must speak the "no
        # pokemon" error rather than crash.
        types = self._assert_routes(
            "what type is it", "get_pokemon_type", padatious=True,
            session_id="pokepedia-en-US-moves-no-context",
        )
        self.assertTrue(set(types) & {"speak", "ovos.utterance.speak"})

    def test_prev_pokemon_context_is_session_isolated(self):
        # Reviewer repro (issue #32 follow-up): device A looks up a Pokémon,
        # device B (a different session) asks a context-only follow-up and
        # must NOT resolve to device A's Pokémon.
        self._assert_intent(
            "tell me about the pokemon charmander", "get_pokemon_info",
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
