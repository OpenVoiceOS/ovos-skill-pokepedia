"""Shared infrastructure for pokepedia intent-routing tests."""
from copy import deepcopy
from unittest.mock import MagicMock

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils.log import LOG
from ovoscope import End2EndTest, get_minicroft

from .fixtures import fake_get_pokemon

SKILL_ID = "ovos-skill-pokepedia.openvoiceos"

_IGNORE = [
    "speak",
    "ovos.common_play.stop.response",
    "common_query.openvoiceos.stop.response",
    "persona.openvoiceos.stop.response",
    "ovos-hivemind-pipeline-plugin.stop.response",
    "stop.openvoiceos.stop.response",
]


class IntentRoutingMixin:
    """Mixin used by per-locale TestCases to assert intent routing.

    Subclasses must define class attribute LANG (e.g. "en-US").
    """

    LANG: str = "en-US"
    SECONDARY_LANGS = ["es-ES", "fr-FR", "it-IT", "pt-PT"]

    @classmethod
    def setUpClass(cls):
        LOG.set_level("DEBUG")
        cls.minicroft = get_minicroft(
            [SKILL_ID], secondary_langs=cls.SECONDARY_LANGS
        )
        loader = cls.minicroft.plugin_skills[SKILL_ID]
        skill = loader.instance
        client = MagicMock()
        client.get_pokemon.side_effect = lambda name: fake_get_pokemon(name)
        skill.api_client = client

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _assert_intent(self, utterance: str, intent_name: str):
        session = Session(f"pokepedia-{self.LANG}-{intent_name}-{hash(utterance)}")
        session.lang = self.LANG
        session.pipeline = [
            "ovos-padatious-pipeline-plugin-high",
            "ovos-adapt-pipeline-plugin-high",
            "ovos-padatious-pipeline-plugin-medium",
            "ovos-adapt-pipeline-plugin-medium",
            "ovos-padatious-pipeline-plugin-low",
            "ovos-adapt-pipeline-plugin-low",
        ]
        message = Message(
            "recognizer_loop:utterance",
            {"utterances": [utterance], "lang": self.LANG},
            {"session": session.serialize()},
        )

        intent_msg_type = f"{SKILL_ID}:{intent_name}"

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=_IGNORE,
            source_message=message,
            activation_points=[intent_msg_type],
            expected_messages=[
                message,
                Message(f"{SKILL_ID}.activate", {}, {"skill_id": SKILL_ID}),
                Message(intent_msg_type, {}, {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.start", {},
                        {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.complete", {},
                        {"skill_id": SKILL_ID}),
                Message("ovos.utterance.handled", {}, {"skill_id": SKILL_ID}),
            ],
        )
        test.execute(timeout=15)
