from __future__ import annotations

from sonicinput.core.services.application_orchestrator import ApplicationOrchestrator
from sonicinput.core.services.config import ConfigKeys
from sonicinput.core.services.events import Events
from sonicinput.speech.null_speech_service import NullSpeechService


class _DummyConfig:
    def __init__(self) -> None:
        self._values = {
            ConfigKeys.TRANSCRIPTION_PROVIDER: "local",
            ConfigKeys.TRANSCRIPTION_LOCAL_AUTO_LOAD: True,
            ConfigKeys.TRANSCRIPTION_LOCAL_MODEL: "paraformer",
        }

    def get_setting(self, key: str, default=None):
        return self._values.get(key, default)


class _RecordingEvents:
    def __init__(self) -> None:
        self.emitted: list[tuple[str, object]] = []

    def on(self, event_name: str, callback):
        return None

    def emit(self, event_name: str, data=None):
        self.emitted.append((event_name, data))


class _DummyState:
    pass


def test_orchestrator_skips_model_loading_when_service_not_running() -> None:
    config = _DummyConfig()
    events = _RecordingEvents()
    orchestrator = ApplicationOrchestrator(
        config_service=config,
        event_service=events,
        state_manager=_DummyState(),
    )

    orchestrator.set_services(
        audio_service=None,
        speech_service=NullSpeechService("test"),
        input_service=None,
        hotkey_service=None,
    )

    orchestrator._init_model_loading()

    emitted_names = [event for event, _ in events.emitted]
    assert Events.MODEL_LOADING_STARTED not in emitted_names
