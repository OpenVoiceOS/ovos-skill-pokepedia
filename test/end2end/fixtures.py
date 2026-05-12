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


def fake_get_pokemon(name: str) -> dict:
    key = (name or "").lower()
    if key in FIXTURES:
        return FIXTURES[key]
    return PIKACHU
