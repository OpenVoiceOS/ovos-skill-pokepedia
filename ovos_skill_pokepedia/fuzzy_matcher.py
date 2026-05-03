"""
Fuzzy matcher for Pokémon names with transcription caching.
Helps resolve STT misheard Pokémon names.
"""

import difflib
import os


class PokemonFuzzyMatcher:
    """Fuzzy matcher for Pokémon names with transcription caching."""

    def __init__(self, vocab_path: str = None):
        self.pokemon_names = []
        self._transcription_cache = {}
        if vocab_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            vocab_path = os.path.join(
                base_dir, "locale", "en-us", "vocab", "pokemon.voc"
            )
        self.load_vocab(vocab_path)
        self._init_common_transcriptions()

    def load_vocab(self, vocab_path: str) -> list:
        """Load Pokémon names from vocab file."""
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                self.pokemon_names = [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            self.pokemon_names = []

    def _init_common_transcriptions(self):
        """Initialize common transcription mappings."""
        common_misphearings = {
            "charizart": "charizard",
            "charizard": "charizard",
            "squirtal": "squirtle",
            "squirtle": "squirtle",
            "bulbasaer": "bulbasaur",
            "bulbasaur": "bulbasaur",
            "pikachu": "pikachu",
            "meowth": "meowth",
            "meowt": "meowth",
            "jigglypuff": "jigglypuff",
            "gengar": "gengar",
            "geodude": "geodude",
            "cubone": "cubone",
            "machamp": "machamp",
            "machop": "machop",
            "bellsprout": "bellsprout",
            "weepinbell": "weepinbell",
            "voltorb": "voltorb",
            "electrode": "electrode",
            "krabby": "krabby",
            "kingler": "kingler",
            "lapras": "lapras",
            "ditto": "ditto",
            "eevee": "eevee",
            "vaporeon": "vaporeon",
            "jolteon": "jolteon",
            "flareon": "flareon",
            "snorlax": "snorlax",
            "articuno": "articuno",
            "zapdos": "zapdos",
            "moltres": "moltres",
            "mewtwo": "mewtwo",
            "mew": "mew",
        }
        self._transcription_cache.update(common_misphearings)

    def cache_transcription(self, heard: str, correct: str):
        """Store a transcription mapping."""
        self._transcription_cache[heard.lower()] = correct.lower()

    def match(self, input_name: str) -> tuple[str, float]:
        """
        Find best matching Pokémon name.

        Args:
            input_name: The name heard from STT

        Returns:
            Tuple of (matched_name, confidence)
            If no good match, returns (input_name, 1.0)
        """
        if not input_name:
            return input_name, 1.0

        input_lower = input_name.lower()

        # Check transcription cache first
        if input_lower in self._transcription_cache:
            matched = self._transcription_cache[input_lower]
            return matched, 1.0

        # Check exact match
        if input_lower in self.pokemon_names:
            return input_lower, 1.0

        # Use fuzzy matching with get_close_matches
        matches = difflib.get_close_matches(
            input_lower, self.pokemon_names, n=1, cutoff=0.6
        )

        if matches:
            confidence = self._calculate_similarity(input_lower, matches[0])
            return matches[0], confidence

        # No match found - return original
        return input_name, 1.0

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings."""
        return difflib.SequenceMatcher(None, s1, s2).ratio()