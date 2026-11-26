"""Intent-routing coverage for en-US.

One canonical utterance per intent family: the ``get_pokemon_info``,
``get_pokemon_type``, ``get_pokemon_evolution`` and ``battle`` file intents.
Each asserts the intent routed and the skill spoke — a drift-immune subset,
never an ordered message sequence. The multi-turn tests cover the follow-up
that names no Pokemon and resolves it from the session context.
"""
from unittest import TestCase
from unittest.mock import MagicMock

from ovoscope import get_minicroft
from ovoscope.routing import TALLY

from ._helpers import (SKILL_ID, IntentRoutingMixin, capture, intent_topic,
                       new_session, session_after, spoken)
from .fixtures import fake_get_evolution_chain, fake_get_pokemon

PADATIOUS = ["ovos-padatious-pipeline-plugin-high",
             "ovos-padatious-pipeline-plugin-medium"]


class TestEnIntentRouting(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def test_info_routes(self):
        self._assert_intent(
            "tell me about the pokemon pikachu", "get_pokemon_info"
        )

    def test_type_routes(self):
        self._assert_intent(
            "what type is the pokemon charizard", "get_pokemon_type"
        )

    def test_battle_routes(self):
        self._assert_routes(
            "who wins pikachu or bulbasaur", "battle.intent"
        )

    def test_battle_speaks_after_match(self):
        self._assert_intent(
            "who wins pikachu or bulbasaur", "battle.intent"
        )

    def test_evolution_routes(self):
        self._assert_intent(
            "what does charmander evolve into", "get_pokemon_evolution"
        )

    def _turn(self, utterance, session):
        return capture(self.minicroft, utterance, self.LANG, session.session_id,
                       session=session)

    def test_moves_follow_up_answers_about_the_previous_pokemon(self):
        """The follow-up names no Pokemon. It must still answer about
        pikachu, from the context the first turn left on the session."""
        session = new_session(self.LANG, "pokepedia-en-US-context-fallback")
        first = self._turn("tell me about the pokemon pikachu", session)
        TALLY.assert_routed("tell me about the pokemon pikachu",
                            intent_topic("get_pokemon_info"),
                            [m.msg_type for m in first])
        session = session_after(first, session)
        self.assertEqual(
            (session.intent_context or {}).get("prev_pokemon", {}).get("value"),
            "pikachu",
            f"turn 1 left no prev_pokemon on the session: {session.intent_context!r}")

        second = self._turn("what about its moves", session)
        TALLY.assert_routed("what about its moves",
                            intent_topic("get_pokemon_moves"),
                            [m.msg_type for m in second])
        self.assertTrue(
            any("pikachu" in u.lower() for u in spoken(second)),
            f"turn 2 did not resolve pikachu from context: {spoken(second)!r}")

    def test_follow_up_in_another_session_does_not_see_the_context(self):
        """Device A looks up charmander. Device B, a different session, asks
        a follow-up and must not hear about charmander."""
        self._turn("tell me about the pokemon charmander",
                   new_session(self.LANG, "pokepedia-en-US-device-a"))
        answer = spoken(self._turn("what about its moves",
                                   new_session(self.LANG, "pokepedia-en-US-device-b")))
        self.assertTrue(answer, "device B never spoke")
        self.assertFalse(any("charmander" in u.lower() for u in answer),
                         f"device B heard device A's Pokemon: {answer!r}")


class TestPronounSlotExclusion(TestCase):
    """``pokemon.blacklist`` on the padatious pipeline, the engine that fills
    a free slot from the utterance. "what does it evolve into" fits "what
    does {pokemon} evolve into"; the exclusion keeps "it" out of the slot,
    so the follow-up asks the API for the remembered Pokemon, never for "it".
    """

    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID], lang="en-US")
        cls.client = MagicMock()
        cls.client.get_pokemon.side_effect = fake_get_pokemon
        cls.client.get_evolution_chain.side_effect = fake_get_evolution_chain
        cls.minicroft.plugin_skills[SKILL_ID].instance.api_client = cls.client

    @classmethod
    def tearDownClass(cls):
        cls.minicroft.stop()

    def test_a_pronoun_never_reaches_the_pokeapi(self):
        session = new_session("en-US", "pokepedia-en-US-pronoun")
        session.pipeline = PADATIOUS
        first = capture(self.minicroft, "tell me about the pokemon pikachu", "en-US",
                        session.session_id, session=session)
        session = session_after(first, session)
        second = capture(self.minicroft, "what does it evolve into", "en-US",
                         session.session_id, session=session)
        matched = [m for m in second if m.msg_type == intent_topic("get_pokemon_evolution")]
        self.assertTrue(matched, f"no evolution match: {[m.msg_type for m in second]}")
        self.assertIsNone(matched[0].data.get("pokemon"))
        self.assertEqual([c.args[0] for c in self.client.get_pokemon.call_args_list],
                         ["pikachu", "pikachu"])
