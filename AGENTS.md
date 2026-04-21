# Project: OVOS Pokémon Battle Assistant

## Role
Senior Python Developer & OVOS Architect

## Target
OpenVoiceOS (OVOS) Skill for Children's Pokémon Battles

## 1. Context & Objective
Create a robust, child-friendly OVOS skill that allows users to query Pokémon data via voice. The skill must interface with the public **PokeAPI** to retrieve stats, types, moves, and abilities. The output must be spoken naturally, suitable for a child, and optimized for battle scenarios (e.g., explaining type advantages).

## 2. Tech Stack & Constraints
- **Runtime**: OpenVoiceOS (OVOS) / Mycroft Core compatible.
- **Language**: Python 3.8+.
- **External API**: PokeAPI (https://pokeapi.co) - No auth required, RESTful JSON.
- **Dependencies**: `requests`, `ovos-utils` (standard OVOS imports).
- **Constraints**:
  - Must handle network errors gracefully (timeout/retry).
  - Responses must be concise for TTS (Text-to-Speech).
  - No complex math in speech; simplify battle logic for kids.
  - Follow OVOS skill directory structure strictly.

## 3. Directory Structure
Follow https://github.com/OpenVoiceOS/ovos-skill-hello-world for the file structure including tests, documentation and workflows.

## 4. Functional Requirements

### A. Intents (Vocabularies)
Define intents to capture:

- `GetPokemonInfo`: "Tell me about [Pokemon Name]"
- `GetPokemonMoves`: "What moves does [Pokemon Name] have?"
- `GetPokemonType`: "What type is [Pokemon Name]?"
- `BattleComparison`: "Who wins between [Pokemon A] and [Pokemon B]?" (Simple logic)

### B. API Integration Logic
Endpoint: https://pokeapi.co/api/v2/pokemon/{name}
Make use of https://github.com/PokeAPI/pokepy

Data Extraction:
- **stats**: Extract HP, Attack, Defense, Speed.
- **types**: List primary and secondary types.
- **moves**: List top 5 most powerful or signature moves.
- **abilities**: Brief description of passive effects.

Error Handling: If API fails, return a fallback message:  
*"I couldn't find that Pokémon right now, try again later."*

### C. Child-Friendly Speech Synthesis
Tone: Enthusiastic, encouraging, simple vocabulary.

Formatting:
- Instead of "Attack stat is 110", say "It has a very strong attack!"
- Explain types simply: "Fire is strong against Grass."

Battle Logic: Implement a simplified damage calculator based on type matchups (e.g., Water > Fire, Fire > Grass). Do not simulate turn-by-turn combat; just predict the winner based on type advantage and base stats.

## 5. Implementation Steps for the Agent

### Step 1: Skeleton Generation
Create the directory structure.
Write `setup.py` with correct OVOS metadata.
Create empty `__init__.py` and `pokemon_skill.py`.

### Step 2: Intent Definition
Generate `vocab/pokemon.voc` with a list of common Pokémon names (Charmander, Bulbasaur, Squirtle, Pikachu, etc.) and generic triggers.
Define the intent logic in `pokemon_skill.py` using `@intent_handler`.

### Step 3: API Client Class
Create a helper class `PokeAPIClient` inside `pokemon_skill.py`.
Implement `fetch_pokemon(name)` with error handling and caching (basic memory cache to reduce API calls).
Implement `get_type_advantage(attacker_type, defender_type)` returning a boolean or string explanation.

### Step 4: Dialog Templates
Create `dialog/pokemon.dialog` with placeholders like `{pokemon_name}`, `{stat_description}`, `{type_list}`.
Ensure sentences flow naturally for TTS (avoid raw JSON dumps).

### Step 5: Testing & Validation
Provide a mock test script to simulate voice commands locally.
Verify that the skill handles unknown Pokémon gracefully.

## 6. Code Quality Standards
- **Docstrings**: Every function must have a docstring explaining inputs/outputs.
- **Logging**: Use `self.log.info()` or `self.log.error()` for debugging.
- **Comments**: Explain complex logic, especially the battle prediction algorithm.
- **Security**: No hardcoded secrets (none needed for PokeAPI).

## 7. Example Interaction Flow

**User**: "Dimmi tutto su Charizard"  
**Agent**: "Charizard è un Pokémon di tipo Fuoco e Volante. È molto veloce e ha un attacco potente. Le sue mosse migliori includono Lanciafiamme e Vento Afferato. In battaglia, è forte contro i Pokémon di tipo Erba e Ghiaccio!"

**User**: "Chi vince tra Pikachu e Gengar?"  
**Agent**: "Pikachu è di tipo Eletttrico, mentre Gengar è Spettro e Veleno. L'Elettrico non è molto efficace contro lo Spettro. Gengar ha statistiche speciali più alte, quindi probabilmente Gengar vincerebbe!"

## 8. Execution Instruction
Start by generating the `setup.py` with the skeleton code from https://github.com/OpenVoiceOS/ovos-skill-hello-world. Then, generate the vocab and dialog files.
