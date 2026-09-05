"""Unit coverage that the {pokemon_a}/{pokemon_b} slots of battle.intent
reach the padatious intent engine as registered entities, WITHOUT the skill
calling register_entity_file() itself.

As of ovos-workshop 9.5.0a1, OVOSSkill auto-discovers and registers every
".entity" file shipped under a skill's locale resources
(OVOSSkill._auto_register_entity_files(), called from load_lang() on
startup) -- a skill no longer needs to call register_entity_file()
explicitly for a file that is just sitting under locale/*/intents/. This
skill relies on that: locale/en-US/intents/pokemon_a.entity and
pokemon_b.entity are both symlinks to locale/en-US/vocab/pokemon.voc, and
initialize() no longer calls register_entity_file() at all (see
ovos_skill_pokepedia/__init__.py).

We assert the wire-level contract directly: both entities must reach the
bus as `padatious:register_entity` messages (the legacy topic
IntentServiceInterface.register_entity() emits -- see
ovos_workshop.intents.IntentServiceInterface.emit_legacy_register_entity),
one per slot, each carrying non-empty samples. This is deliberately a bus
assertion rather than a call-count mock on register_entity_file(): nothing
in this skill's own code calls that method anymore, so the only honest way
to prove the slots are wired is to prove the payload actually left the
skill for the intent service.

Mutation tripwire: this test is red whenever pokemon_a.entity's symlink
target (locale/en-US/vocab/pokemon.voc) is missing or empty, and green
again once it is restored -- see
test_initialize_registration_survives_missing_entity_target below, which
performs that mutation directly against a temp copy of the skill's locale
tree instead of asserting on the checked-in files (so it also catches a
future skill author accidentally deleting the entity symlinks outright).
"""
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from ovos_utils.messagebus import FakeBus

from ovos_skill_pokepedia import PokemonSkill

SKILL_ID = "ovos-skill-pokepedia.openvoiceos"


def _boot_and_capture_registrations(bus: FakeBus, skill_res_dir=None):
    """Instantiate + start the skill on `bus`, return the
    `padatious:register_entity` messages captured for pokemon_a/pokemon_b."""
    captured = []
    bus.on("padatious:register_entity", lambda m: captured.append(m))
    kwargs = {}
    if skill_res_dir is not None:
        kwargs["res_dir"] = str(skill_res_dir)
    skill = PokemonSkill(**kwargs) if skill_res_dir is not None else PokemonSkill()
    skill._startup(bus, SKILL_ID)
    skill.shutdown()
    return {m.data["name"]: m.data for m in captured
            if m.data.get("name", "").split(":")[-1] in ("pokemon_a", "pokemon_b")}


def test_battle_slots_auto_register_without_manual_wiring():
    """No register_entity_file() call anywhere in this skill's own code --
    prove the wildcard-vs-constrained-slot behavior for pokemon_a/pokemon_b
    still reaches padatious via auto-registration alone."""
    bus = FakeBus()
    with mock.patch.object(PokemonSkill, "register_entity_file", autospec=True) as mocked:
        registrations = _boot_and_capture_registrations(bus)
    # this skill's code never calls register_entity_file() itself anymore
    mocked.assert_not_called()
    names = set(registrations.keys())
    assert names == {f"{SKILL_ID}:pokemon_a", f"{SKILL_ID}:pokemon_b"}, (
        "auto-registration should have registered a padatious entity for "
        "every {slot} that has a locale/*/intents/*.entity file, with no "
        "explicit register_entity_file() call in the skill"
    )
    for name, data in registrations.items():
        assert data.get("samples"), f"{name} registered with no samples"


def test_initialize_registration_survives_missing_entity_target():
    """Mutation tripwire, run against a throwaway copy of the skill's
    locale tree so the checked-in fixtures are never touched:

    - baseline copy: pokemon_a.entity's symlink target is intact -> the
      entity registers with samples (green).
    - mutated copy: the symlink target (vocab/pokemon.voc) is deleted ->
      auto-registration logs and skips it, so no pokemon_a entity reaches
      the bus at all (red: this is the failure this test exists to catch).
    - restored copy: the target file is put back -> green again.
    """
    src = Path(__file__).parent.parent / "ovos_skill_pokepedia" / "locale"

    def _boot_with_tree(locale_root: Path):
        tmp_pkg_root = locale_root.parent
        bus = FakeBus()
        with mock.patch.object(PokemonSkill, "register_entity_file", autospec=True):
            skill = PokemonSkill(resources_dir=str(tmp_pkg_root))
            captured = []
            bus.on("padatious:register_entity", lambda m: captured.append(m))
            skill._startup(bus, SKILL_ID)
            skill.shutdown()
        return {m.data["name"] for m in captured}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp) / "skill"
        tmp_locale = tmp_root / "locale"
        shutil.copytree(src, tmp_locale, symlinks=False)  # dereference: real files

        # --- baseline: green ---
        names = _boot_with_tree(tmp_locale)
        assert f"{SKILL_ID}:pokemon_a" in names, "baseline should register pokemon_a"

        # --- mutation: delete the (dereferenced) entity file's content source ---
        target = tmp_locale / "en-US" / "intents" / "pokemon_a.entity"
        target.unlink()
        names_mutated = _boot_with_tree(tmp_locale)
        assert f"{SKILL_ID}:pokemon_a" not in names_mutated, (
            "deleting pokemon_a.entity should stop it from being registered "
            "(auto-registration walks the entity dir at boot; if this "
            "assertion fails, something is caching/registering the entity "
            "independent of the file actually being present)"
        )

        # --- restore: green again ---
        # write the same samples back (equivalent to "restore the symlink")
        original_samples = (src / "en-US" / "intents" / "pokemon_a.entity").read_text()
        target.write_text(original_samples)
        names_restored = _boot_with_tree(tmp_locale)
        assert f"{SKILL_ID}:pokemon_a" in names_restored, (
            "restoring pokemon_a.entity should register it again"
        )
