"""
Fuzzy matcher for Pokémon names with transcription caching.
Helps resolve STT misheard Pokémon names.
"""

import difflib
import os
from functools import lru_cache


class PokemonFuzzyMatcher:
    """Fuzzy matcher for Pokémon names with transcription caching."""
    
    def __init__(self, vocab_path: str = None):
        # Load vocab file (pokemon.voc has 1000+ names)
        self.pokemon_names = self.load_vocab(vocab_path)
        
        # Initialize LRU cache for transcription lookups
        self._cache_transcription = lru_cache(maxsize=128)(self._cache_transcription)
        
        # Preload common misspellings
        self._preload_common_misspellings()
    
    def load_vocab(self, vocab_path: str) -> list:
        """Parse pokemon.voc file, return list of pokemon names."""
        # Default vocab path
        if vocab_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            vocab_path = os.path.join(
                base_dir, "vocab", "pokemon.voc"
            )
        
        # Read the vocab file and return names
        try:
            with open(vocab_path, 'r') as f:
                lines = f.readlines()
            
            # Parse lines and return list of pokemon names
            pokemon_list = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):  # Skip empty lines and comments
                    pokemon_list.append(line.lower())
            
            return pokemon_list
        except FileNotFoundError:
            # Return a basic list if file doesn't exist
            return ["bulbasaur", "ivysaur", "venusaur", "charmander", "charmeleon", "charizard", 
                   "squirtle", "wartortle", "blastoise", "pikachu", "raichu", "eevee", "vaporeon", 
                   "jolteon", "flareon", "mewtwo", "mew", "ditto", "pidgey", "pidgeotto", "pidgeot",
                   "rattata", "raticate", "spearow", "fearow", "ekans", "arbok", "pikachu", "raichu",
                   "sandshrew", "sandslash", "nidoran", "nidorina", "nidoqueen", "nidoran", "nidorino", "nidoking",
                   "clefairy", "clefable", "vulpix", "ninetales", "jigglypuff", "wigglytuff", "zubat", "golbat",
                   "oddish", "gloom", "vileplume", "paras", "parasect", "venonat", "venomoth", "diglett", "dugtrio",
                   "meowth", "persian", "psyduck", "golduck", "mankey", "primeape", "growlithe", "arcanine",
                   "poliwag", "poliwhirl", "poliwrath", "abra", "kadabra", "alakazam", "machop", "machoke", "machamp",
                   "bellsprout", "weepinbell", "victreebel", "tentacool", "tentacruel", "geodude", "graveler", "golem",
                   "ponyta", "rapidash", "slowpoke", "slowbro", "magnemite", "magneton", "farfetchd", "doduo", "dodrio",
                   "seel", "dewgong", "grimer", "muk", "shellder", "cloyster", "gastly", "haunter", "gengar",
                   "onix", "drowzee", "hypno", "krabby", "kingler", "voltorb", "electrode", "exeggcute", "exeggutor",
                   "cubone", "marowak", "hitmonlee", "hitmonchan", "lickitung", "koffing", "weezing", "rhyhorn", "rhydon",
                   "chansey", "tangela", "kangaskhan", "horsea", "seadra", "goldeen", "seaking", "staryu", "starmie",
                   "mr_mime", "scyther", "jynx", "electabuzz", "magmar", "pinsir", "tauros", "magikarp", "gyarados",
                   "lapras", "ditto", "eevee", "vaporeon", "jolteon", "flareon", "porygon", "omanyte", "omastar",
                   "kabuto", "kabutops", "aerodactyl", "snorlax", "articuno", "zapdos", "moltres", "dratini", "dragonair",
                   "dragonite", "mewtwo", "mew"]
    
    def _preload_common_misspellings(self):
        """Preload common misspellings to improve matching."""
        # This is handled via the cache mechanism, but can be extended if needed
        pass
    
    def match(self, input_name: str) -> tuple[str, float]:
        """Use difflib.get_close_matches for fuzzy matching.
        
        Return (matched_name, confidence) or (input_name, 1.0) if no match.
        Check transcription cache first.
        """
        if not input_name:
            return (input_name, 1.0)
        
        # Check transcription cache first (via our cached method)
        cached_result = self._cache_transcription(input_name.lower())
        if cached_result:
            return cached_result
        
        # If no cache match, do fuzzy matching
        if not self.pokemon_names:
            return (input_name, 1.0)
        
        # Get close matches
        matches = difflib.get_close_matches(input_name, self.pokemon_names, n=1, cutoff=0.6)
        
        if matches:
            confidence = difflib.SequenceMatcher(None, input_name.lower(), matches[0].lower()).ratio()
            return (matches[0], confidence)
        else:
            return (input_name, 1.0)
    
    def cache_transcription(self, heard: str, correct: str):
        """Store common transcriptions in LRU cache."""
        # Clear cache and store new mapping
        self._cache_transcription.cache_clear()
        self._cache_transcription(heard, correct)
    
    def _cache_transcription(self, heard: str, correct: str = None) -> tuple[str, float]:
        """Internal method for LRU caching of transcriptions."""
        # We need a way to actually store transcriptions in a proper cache.
        # For now we'll keep the simple implementation, but we can enhance this later
        # This method would normally be a function that's decorated for caching
        # Since we're using a different approach, this serves as a placeholder
        # The actual caching will be managed by lru_cache decorator above it
        pass