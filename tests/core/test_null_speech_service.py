from __future__ import annotations

import numpy as np
import pytest

from sonicinput.speech.null_speech_service import NullSpeechService


def test_null_speech_service_properties() -> None:
    service = NullSpeechService("unavailable")

    assert service.is_running is False
    assert service.is_model_loaded is False
    assert service.get_available_models() == []
    assert service.get_available_models_async() == []


def test_null_speech_service_transcribe_raises() -> None:
    service = NullSpeechService("nope")

    with pytest.raises(RuntimeError):
        service.transcribe(np.zeros(1, dtype=np.float32))
