# Project: OVOS Pokémon Battle Assistant

OVOS skill that queries [PokeAPI](https://pokeapi.co) for Pokémon stats, types,
moves, and predicts simple type-advantage-based battle outcomes. Child-friendly
TTS-oriented responses. Supported locales: en-US, es-ES, fr-FR, it-IT.

---

## Skill lifecycle rules

1. **Defaults must be assigned BEFORE `super().__init__()`** in the skill
   constructor. `OVOSSkill.__init__` runs the full skill lifecycle (including
   `initialize()`) via the super call. Assigning `self.api_client = None`
   *after* `super().__init__()` wipes the value `initialize()` set and every
   intent silently falls back to `error.not.found`.

2. **There is no `self._translate()` on OVOSSkill.** Translations live in
   `locale/<lang>/dialog/phrases.value` and are read with
   `self.resources.load_named_value_file("phrases")`.

3. **Fuzzy matching uses `ovos_utils.parse.match_one` directly.** No helper
   class. `_resolve_pokemon_name` sources names from `PokemonName.voc` via
   `self.resources.load_vocabulary_file("PokemonName")`.

4. **Adapt entity name == .voc filename.** Voc files are named exactly after
   the entity required by the IntentBuilder: `TellMeKeyword.voc`,
   `MovesKeyword.voc`, `TypeKeyword.voc`, `PokemonName.voc`.

5. **Locale dirs are BCP-47** (`en-US`, not `en-us`).

6. **Padatious capture groups need a non-slot token between them.**
   `{PokemonA} {PokemonB}` is invalid syntax. Every `battle.intent` line uses
   a real connector word (`and`, `vs`, `or`, `between`, `against`, `y`,
   `contra`, `entre`, `et`, `ou`, `e`, `tra`, `o`).

---

## Intent pipeline split

Each intent uses exactly one pipeline. Do not duplicate intents across both.

| Intent              | Engine    | Source files                              |
|---------------------|-----------|-------------------------------------------|
| `GetPokemonInfo`    | Adapt     | `TellMeKeyword.voc` + `PokemonName.voc`   |
| `GetPokemonMoves`   | Adapt     | `MovesKeyword.voc` + `PokemonName.voc`    |
| `GetPokemonType`    | Adapt     | `TypeKeyword.voc` + `PokemonName.voc`     |
| `BattleComparison`  | Padatious | `battle.intent` + `PokemonA.entity` + `PokemonB.entity` |

Info/moves/type each have an unambiguous trigger keyword and a single entity
slot — Adapt is deterministic and needs no training data churn for short
variants like "moves pikachu". Battle needs two slots with varied connector
words across four languages — Padatious handles that natively.

When adding a new intent, pick one engine. Do not write both a `.voc`-driven
IntentBuilder and an `.intent` file for the same handler.

---

## Resource layout

```
ovos_skill_pokepedia/locale/<lang>/
├── dialog/
│   ├── *.dialog           # spoken responses
│   └── phrases.value      # internal-key → localized phrase (CSV)
├── intents/
│   ├── battle.intent      # padatious training utterances (battle only)
│   ├── PokemonA.entity    # padatious slot values
│   └── PokemonB.entity    # padatious slot values
└── vocab/
    ├── TellMeKeyword.voc  # adapt keywords (info trigger)
    ├── MovesKeyword.voc   # adapt keywords (moves trigger)
    ├── TypeKeyword.voc    # adapt keywords (type trigger)
    └── PokemonName.voc    # adapt entity values + fuzzy-match source
```

Voc filenames must match the entity name used in `IntentBuilder.require(...)`.
Entity filenames must match the slot name used in `.intent` files.

---

## API client injection

`PokemonSkill.client` is a property exposing `self.api_client`. Tests and
power users override it post-load:

```python
skill.api_client = MagicMock()
skill.api_client.get_pokemon.side_effect = lambda name: FIXTURE[name.lower()]
```

This is the supported way to mock the network in tests. Do not mock
`requests` at the module level.

---

## Tests

```bash
pip install -e . -r test/requirements.txt
pytest test/                        # 111 tests
pytest test/end2end/ -v             # 93 ovoscope intent-routing tests
pytest test/test_pokepedia.py -v    # 18 helper unit tests
```

### Conventions

- **One test method per planned utterance.** Intent coverage, not code
  coverage — a failure must name the exact phrasing and language that
  doesn't route.
- **No bus-bypassing tests.** Never instantiate `PokemonSkill(bus=None)` and
  call handlers directly. Use ovoscope's `End2EndTest` + `get_minicroft`.
- The shared helper at `test/end2end/_helpers.py` injects a mocked
  `api_client` in `setUpClass` so no real HTTP traffic happens.
- The session pipeline interleaves Adapt and Padatious at each priority
  tier — each intent matches in its own engine without ranking games.

---

## Code quality

- No `try: ... except Exception: pass` to silence bugs. Let failures surface.
- No hardcoded fallback lists for data that belongs in `.voc` / `.entity`
  files. If the resource is missing, fail loudly.
- Use OVOS resource loading: `self.voc_list`, `self.resources.load_vocabulary_file`,
  `self.resources.load_named_value_file`, `self.dialog_renderer.render` —
  they handle locale fallback and caching.
- No emojis in code unless explicitly requested.

---

## Version management

Versions in `manifest.json` and `ovos_skill_pokepedia/version.py` must stay
in sync. Before merging to main: bump both. Format `MAJOR.MINOR.BUILD`;
alpha versions set `VERSION_ALPHA > 0`.
