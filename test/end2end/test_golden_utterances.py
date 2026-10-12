"""Golden rows in every locale route to their intent on the m2v pipeline.

For each ``golden_utterances_<lang>.jsonl`` in this directory, one MiniCroft
loads the real skill in that language on the m2v prototype pipeline, the
model2vec engine built at boot from the skill's own ``.intent`` files. Each
row's utterance goes through that pipeline's high, medium and low tiers in
order, and the row passes when the first tier to match names its
``intent_label``. The engine embeds the utterance, so a row that no template
spells out word for word still matches when it means the same thing. Only the
match is computed: no row is dispatched, so no PokeAPI call is made.

Each ``negative_utterances_<lang>.jsonl`` holds requests for other skills
(timers, the weather, music, the time, general knowledge). They run in the
same MiniCroft and must match no intent of this skill.

Each locale must match at least ``MIN_MATCH_RATE`` of its golden rows, and at
least ``MIN_MATCHED_ROWS_PER_INTENT`` rows of each intent. A locale listed in
``GOLDEN_LOCALE_GAPS`` is a non-strict xfail on the rate only: it still fails
when an intent has no matched row, or when its rate falls more than
``GAP_RATE_TOLERANCE`` below the rate stored in its entry. A negative row that
matches this skill fails the locale, unless ``NEGATIVE_KNOWN_CLAIMS`` lists
that claim. All rows run, including rows marked ``needs_manual`` or
``machine_generated``, and the test prints every row that misses with the
intent that matched instead.
"""
import json
from functools import cache
from pathlib import Path

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import SessionManager
from ovoscope import M2V_PUBLISHED_MODEL, get_m2v_minicroft
from ovoscope.golden_minicroft import warm_m2v_models

SKILL_ID = "ovos-skill-pokepedia.openvoiceos"
M2V_PROTOTYPE = "ovos-m2v-prototype-pipeline"
TIERS = ("high", "medium", "low")
# m2v gives some rows a different answer on each boot, so the test gates on
# the share of rows that match per locale, not on each row.
MIN_MATCH_RATE = 0.8
# A locale also fails when any of its intents has fewer matched rows than this.
MIN_MATCHED_ROWS_PER_INTENT = 1
# Locales whose locale files do not yet reach MIN_MATCH_RATE on m2v:
# {lang: (measured rate, reason)}. The per-intent floor still applies to them.
# The prototypes fill {pokemon} from a 1024-name .entity list, and the engine keeps
# 2000 samples per intent, so which names an intent kept decides the match: a dev
# template, "describe the pokemon <name>", reaches get_pokemon_info for 19 of 40
# names on dev. Rates are the lower of two measured runs after the linguonnx lines.
_NAME_GAP = ("m2v matches the pokemon name more than the request; natural rows "
             "without the word pokemon fall below the low tier")
GOLDEN_LOCALE_GAPS = {
    "ca-ES": (0.688, _NAME_GAP),
    "da-DK": (0.682, _NAME_GAP),
    "de-DE": (0.625, _NAME_GAP),
    "en-US": (0.600, _NAME_GAP),
    "es-CO": (0.625, _NAME_GAP),
    "es-ES": (0.625, _NAME_GAP),
    "eu-ES": (0.688, _NAME_GAP),
    "fa-IR": (0.750, _NAME_GAP),
    "fr-FR": (0.625, _NAME_GAP),
    "gl-ES": (0.688, _NAME_GAP),
    "it-IT": (0.625, _NAME_GAP),
    "nl-NL": (0.750, _NAME_GAP),
    "pl-PL": (0.562, _NAME_GAP),
    "pt-BR": (0.562, _NAME_GAP),
    "pt-PT": (0.562, _NAME_GAP),
    "ru-RU": (0.688, _NAME_GAP),
    "sv-SE": (0.625, _NAME_GAP),
}
GAP_RATE_TOLERANCE = 0.10
# Locales where the published m2v model cannot keep other skills' requests
# away from this skill. Their negative test is a non-strict xfail.
NEGATIVE_ENGINE_GAPS = {
    "fa-IR": "the published m2v model claims 3 of 5 off-skill requests, a different intent per boot",
    "ru-RU": "the published m2v model claims all 5 off-skill requests, a different intent per boot",
}
# Negative rows that m2v claimed for this skill in two separate runs. A listed
# claim is allowed, not required, so a row that flips between boots does not
# fail the test. Any other claim fails the locale.
NEGATIVE_KNOWN_CLAIMS = {
    "de-DE": {"wer ist der präsident von frankreich": "battle"},
    "pl-PL": {"włącz jakąś muzykę": "get_pokemon_moves",
              "kto jest prezydentem francji": "battle"},
    "sv-SE": {"vem är frankrikes president": "get_pokemon_info"},
}
END2END_DIR = Path(__file__).parent
LOCALE_DIR = END2END_DIR.parents[1] / "ovos_skill_pokepedia" / "locale"
DEFAULT_LANG_AT_IMPORT = SessionManager.get_default_session().lang


def _rows_by_lang(prefix):
    rows = {}
    for path in sorted(END2END_DIR.glob(f"{prefix}_*.jsonl")):
        lang = path.stem.removeprefix(f"{prefix}_")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                row = json.loads(line)
                assert row["lang"] == lang, f"{path.name}:{number} has lang {row['lang']!r}"
                rows.setdefault(lang, []).append(row)
    return rows


ROWS = _rows_by_lang("golden_utterances")
NEGATIVE_ROWS = _rows_by_lang("negative_utterances")


def _intent_files(lang):
    return {p.stem for p in (LOCALE_DIR / lang).rglob("*.intent")}


def _matched_intent(engine, utterance, lang):
    """Return the bare intent name the first answering tier matched, or None."""
    message = Message("recognizer_loop:utterance",
                      {"utterances": [utterance], "lang": lang}, {"lang": lang})
    match = next(filter(None, (getattr(engine, f"match_{tier}")([utterance], lang, message)
                               for tier in TIERS)), None)
    return match.match_type.removesuffix(".intent") if match else None


@cache
def _matches(lang):
    """Boot the skill on m2v in ``lang`` once; return what each golden and negative row matches."""
    minicroft = get_m2v_minicroft([SKILL_ID], model=M2V_PUBLISHED_MODEL,
                                  lang=lang, classifier=False)
    try:
        warm_m2v_models(minicroft)
        engine = minicroft.intents.pipeline_plugins[M2V_PROTOTYPE]
        golden = [_matched_intent(engine, row["utterance"], lang) for row in ROWS[lang]]
        negative = [_matched_intent(engine, row["utterance"], lang)
                    for row in NEGATIVE_ROWS.get(lang, [])]
    finally:
        minicroft.stop()
    return golden, negative


@pytest.mark.timeout(900)
@pytest.mark.parametrize("lang", sorted(ROWS))
def test_golden_rows_match_their_intent(lang):
    rows = ROWS[lang]
    matched, _ = _matches(lang)
    misses = []
    hits = {row["intent_label"]: 0 for row in rows}
    for row, got in zip(rows, matched):
        if got == f"{SKILL_ID}:{row['intent_label']}":
            hits[row["intent_label"]] += 1
        else:
            misses.append(f"{row['utterance']!r}: expected {row['intent_label']}, got {got}")
    starved = sorted(label for label, count in hits.items()
                     if count < MIN_MATCHED_ROWS_PER_INTENT)
    rate = 1 - len(misses) / len(rows)
    print(f"[{lang}] {rate:.1%} of {len(rows)} rows match", *misses, sep="\n  ")
    if starved:
        print(f"[{lang}] intents below {MIN_MATCHED_ROWS_PER_INTENT} matched rows: {starved}")
    assert not starved, (
        f"[{lang}] intents below {MIN_MATCHED_ROWS_PER_INTENT} matched rows: {starved}"
    )
    if lang in GOLDEN_LOCALE_GAPS:
        measured, reason = GOLDEN_LOCALE_GAPS[lang]
        assert rate >= measured - GAP_RATE_TOLERANCE, (
            f"[{lang}] {rate:.1%} of rows match, more than {GAP_RATE_TOLERANCE:.0%} "
            f"below the measured {measured:.1%}"
        )
        if rate < MIN_MATCH_RATE:
            pytest.xfail(f"[{lang}] {rate:.1%} below {MIN_MATCH_RATE:.0%}: {reason}")
    assert rate >= MIN_MATCH_RATE, (
        f"[{lang}] {rate:.1%} of rows match, below {MIN_MATCH_RATE:.0%}:\n  " + "\n  ".join(misses)
    )


@pytest.mark.timeout(900)
@pytest.mark.parametrize("lang", [
    pytest.param(lang, marks=pytest.mark.xfail(reason=NEGATIVE_ENGINE_GAPS[lang], strict=False))
    if lang in NEGATIVE_ENGINE_GAPS else lang
    for lang in sorted(NEGATIVE_ROWS)
])
def test_negative_rows_match_no_skill_intent(lang):
    rows = NEGATIVE_ROWS[lang]
    known = NEGATIVE_KNOWN_CLAIMS.get(lang, {})
    _, matched = _matches(lang)
    claims = [(row["utterance"], got.removeprefix(f"{SKILL_ID}:"))
              for row, got in zip(rows, matched)
              if got and got.startswith(f"{SKILL_ID}:")]
    unknown = [f"{utterance!r}: matched {intent}" for utterance, intent in claims
               if known.get(utterance) != intent]
    print(f"[{lang}] {len(claims)} of {len(rows)} negative rows claimed, "
          f"{len(unknown)} not in NEGATIVE_KNOWN_CLAIMS", *unknown, sep="\n  ")
    assert not unknown, f"[{lang}] negative rows matched this skill:\n  " + "\n  ".join(unknown)


def test_every_negative_file_has_a_golden_file():
    assert set(NEGATIVE_ROWS) <= set(ROWS), sorted(set(NEGATIVE_ROWS) - set(ROWS))


def test_every_shipping_locale_has_a_golden_file():
    shipping = {d.name for d in LOCALE_DIR.iterdir() if d.is_dir() and _intent_files(d.name)}
    assert set(ROWS) == shipping, f"golden files {sorted(set(ROWS) ^ shipping)} differ from shipping locales"


def test_every_locale_ships_every_en_us_intent():
    """A deleted .intent file fails here, whatever the golden rows or gap entries say."""
    reference = _intent_files("en-US")
    assert reference, "en-US ships no .intent file"
    missing = {d.name: sorted(reference - _intent_files(d.name))
               for d in LOCALE_DIR.iterdir() if d.is_dir()}
    missing = {lang: names for lang, names in missing.items() if names}
    assert not missing, f"locales missing en-US intents: {missing}"


def test_every_golden_label_is_a_shipped_intent():
    for lang, rows in ROWS.items():
        unknown = sorted({row["intent_label"] for row in rows} - _intent_files(lang))
        assert not unknown, f"[{lang}] rows name intents the locale does not ship: {unknown}"


def test_every_shipped_intent_has_golden_rows():
    for lang, rows in ROWS.items():
        uncovered = sorted(_intent_files(lang) - {row["intent_label"] for row in rows})
        assert not uncovered, f"[{lang}] intents with no golden row: {uncovered}"


def test_rows_carry_no_engine_field():
    for lang, rows in ROWS.items():
        for row in rows:
            engine_keys = {"intent_type", "intent_method"} & set(row)
            assert not engine_keys, f"[{lang}] {row['utterance']!r} carries {sorted(engine_keys)}"


def test_the_module_leaves_the_process_on_its_default_language():
    """A MiniCroft booted in one locale writes the process default language
    back when it stops. If it did not, every MiniCroft booted later in the
    same pytest process would load the skill in the last locale and route
    nothing. This test runs after every locale and reads that value."""
    assert SessionManager.get_default_session().lang == DEFAULT_LANG_AT_IMPORT
