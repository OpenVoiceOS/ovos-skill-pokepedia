# OVOS Pokémon Battle Assistant

A child-friendly OpenVoiceOS (OVOS) skill that allows users to query Pokémon data via voice commands. The skill interfaces with the public **PokeAPI** to retrieve stats, types, moves, and abilities, and provides simplified battle predictions.

Originally authored by [denix](https://codeberg.org/denix/ovos-skill-pokepedia) on Codeberg; this fork lives under OpenVoiceOS for ongoing maintenance.

## Features

- **Get Pokémon Info**: "Tell me about [Pokemon Name]"
- **Get Pokémon Moves**: "What moves does [Pokemon Name] have?"
- **Get Pokémon Type**: "What type is [Pokemon Name]?"
- **Battle Comparison**: "Who wins between [Pokemon A] and [Pokemon B]?"

## Installation

```bash
pip install ovos-skill-pokepedia
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
pytest test/
```

## License

MIT License