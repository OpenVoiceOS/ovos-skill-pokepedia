"""Minimal PokeAPI-shaped fixtures for ovoscope intent tests."""


def _pokemon(name, pid, attack, speed, defense, hp, types, moves):
    return {
        "name": name,
        "id": pid,
        "stats": [
            {"stat": {"name": "attack"}, "base_stat": attack},
            {"stat": {"name": "speed"}, "base_stat": speed},
            {"stat": {"name": "defense"}, "base_stat": defense},
            {"stat": {"name": "hp"}, "base_stat": hp},
        ],
        "types": [{"type": {"name": t}} for t in types],
        "moves": [{"move": {"name": m}} for m in moves],
    }


PIKACHU = _pokemon(
    "pikachu", 25, 55, 90, 40, 35,
    ["electric"],
    ["thunder-shock", "quick-attack", "thunderbolt", "iron-tail", "agility"],
)

CHARMANDER = _pokemon(
    "charmander", 4, 52, 65, 43, 39,
    ["fire"],
    ["scratch", "ember", "growl", "leer", "smokescreen"],
)

FIXTURES = {
    "pikachu": PIKACHU,
    "charmander": CHARMANDER,
}

# Minimal PokeAPI-shaped evolution chains: pikachu is a mid-chain stage
# (evolves from pichu, into raichu), charmander is chain-start (evolves
# into charmeleon).
EVOLUTION_CHAINS = {
    "pikachu": {
        "species": {"name": "pichu"},
        "evolves_to": [
            {
                "species": {"name": "pikachu"},
                "evolves_to": [
                    {"species": {"name": "raichu"}, "evolves_to": []}
                ],
            }
        ],
    },
    "charmander": {
        "species": {"name": "charmander"},
        "evolves_to": [
            {
                "species": {"name": "charmeleon"},
                "evolves_to": [
                    {"species": {"name": "charizard"}, "evolves_to": []}
                ],
            }
        ],
    },
}


def fake_get_pokemon(name: str) -> dict:
    key = (name or "").lower()
    if key in FIXTURES:
        return FIXTURES[key]
    return PIKACHU


def fake_get_evolution_chain(name: str) -> dict:
    key = (name or "").lower()
    return EVOLUTION_CHAINS.get(key, EVOLUTION_CHAINS["pikachu"])
