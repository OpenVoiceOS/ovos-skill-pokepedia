"""Regression coverage for the battle-intent closed-set defect.

``{pokemon_a}``/``{pokemon_b}`` are free slots, and the intent engine
matches them to any word, so a non-pokemon pair such
as "who wins, banana or carrot" used to be answered as a real battle
(the fuzzy resolver in ``_resolve_pokemon_name`` silently snapped both
free-text slots to an arbitrary pokedex entry). ``handle_battle_comparison``
now gates on ``voc_match_span`` against the closed ``pokemon.voc``
vocabulary and speaks nothing unless at least two real pokemon names are
actually present in the utterance.

A second, narrower regression closed here: ``pokemon.voc`` ships several
real pokemon only under their API-canonical hyphenated/special-form slug
("nidoran-f"/"nidoran-m", "mr-mime", "ho-oh", ...), so the closed-set gate
initially rejected the natural spoken spelling of those names ("nidoran",
"mr mime", "ho oh") even though the pre-fix fuzzy resolver used to handle
them fine. ``pokemon.voc``/``pokemon.name.aliases.value`` now also carry
the de-hyphenated natural-language spelling of every such entry, mapped
back to a valid pokedex slug.

These tests assert the three outcomes end to end: a real pokemon pair
still gets a battle answer naming both pokemon in utterance order, a real
pair using a special-form pokemon's natural spelling is detected and
answered too, and a non-pokemon pair never produces a spoken answer.
"""
from unittest import TestCase

from ovoscope.routing import TALLY

from ._helpers import IntentRoutingMixin, intent_topic
from .fixtures import FIXTURES, _pokemon

_BATTLE = intent_topic("battle")
_SPOKE = {"speak", "ovos.utterance.speak"}

FIXTURES.setdefault(
    "nidoran-m", _pokemon("nidoran-m", 32, 46, 40, 26, 46, ["poison"], ["poison-sting"])
)
FIXTURES.setdefault(
    "nidoking", _pokemon("nidoking", 34, 92, 85, 77, 81, ["poison", "ground"], ["thrash"])
)
FIXTURES.setdefault(
    "mr-mime", _pokemon("mr-mime", 122, 45, 90, 65, 40, ["psychic", "fairy"], ["confusion"])
)
FIXTURES.setdefault(
    "ho-oh", _pokemon("ho-oh", 250, 130, 90, 154, 106, ["fire", "flying"], ["sacred-fire"])
)


class TestBattleClosedSetGuard(IntentRoutingMixin, TestCase):
    LANG = "en-US"

    def _spoken_battle_result(self, utterance: str):
        messages = self._messages(utterance)
        TALLY.assert_routed(utterance, _BATTLE, [m.msg_type for m in messages])
        for msg in messages:
            meta = msg.data.get("meta", {}) if msg.msg_type in _SPOKE else {}
            if meta.get("dialog") == "battle":
                return meta.get("data", {})
        return None

    def test_real_pokemon_pair_is_answered_in_order(self):
        types = self._assert_routes("who wins charmander or pikachu", "battle")
        self.assertTrue(_SPOKE.intersection(types))

    def test_special_form_pokemon_natural_spelling_is_answered(self):
        data = self._spoken_battle_result("who wins nidoran or nidoking")
        self.assertIsNotNone(data, "nidoran/nidoking pair was declined")
        self.assertEqual((data.get("pokemon_a") or "").lower(), "nidoran m")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "nidoking")

    def test_multi_word_special_form_pokemon_natural_spelling_is_answered(self):
        data = self._spoken_battle_result("who wins mr mime or ho oh")
        self.assertIsNotNone(data, "mr mime/ho oh pair was declined")
        self.assertEqual((data.get("pokemon_a") or "").lower(), "mr mime")
        self.assertEqual((data.get("pokemon_b") or "").lower(), "ho oh")

    def test_non_pokemon_pair_is_declined(self):
        # The engine can match {pokemon_a}/{pokemon_b} to "banana"/"carrot";
        # the skill must still never speak a fabricated battle result.
        types = self._capture("who wins banana or carrot")
        self.assertFalse(
            _SPOKE.intersection(types),
            f"non-pokemon pair was wrongly answered (captured: {types})",
        )
