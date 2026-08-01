# OVOS Pokémon Battle Assistant

This is an OpenVoiceOS (OVOS) skill for child-friendly voice queries about Pokémon. The skill gets stats, types, moves, and abilities from the public [PokeAPI](https://pokeapi.co), and it gives simple battle predictions based on type advantage. It supports en-US, es-ES, fr-FR, it-IT, and pt-PT.

[denix](https://codeberg.org/denix/ovos-skill-pokepedia) wrote the original skill on Codeberg. This fork lives under OpenVoiceOS for ongoing maintenance.

## Features

- **Get Pokémon info**: "Tell me about [Pokemon Name]"
- **Get Pokémon moves**: "What moves does [Pokemon Name] have?"
- **Get Pokémon type**: "What type is [Pokemon Name]?"
- **Battle comparison**: "Who wins between [Pokemon A] and [Pokemon B]?"

## Installation

```bash
pip install ovos-skill-pokepedia
```

## Development

```bash
# Install the skill and test dependencies
pip install -e . -r test/requirements.txt

# Run the tests
pytest test/
```

## Related projects

- [OpenVoiceOS/OVOS-workshop](https://github.com/OpenVoiceOS/OVOS-workshop): the skill framework this skill builds on.
- [OpenVoiceOS](https://github.com/OpenVoiceOS): the org that maintains this fork.

## License

MIT License
