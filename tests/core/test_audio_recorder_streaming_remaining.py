import sys
import threading
import types

import numpy as np


def _ensure_pyaudio_importable() -> None:
    try:
        import pyaudio  # noqa: F401
    except ImportError:
        pyaudio_stub = types.ModuleType("pyaudio")
        pyaudio_stub.paInt16 = 8

        class PyAudio:  # pragma: no cover
            def __init__(self, *args, **kwargs):
                pass

        pyaudio_stub.PyAudio = PyAudio
        sys.modules["pyaudio"] = pyaudio_stub


_ensure_pyaudio_importable()

from sonicinput.audio.recorder import AudioRecorder  # noqa: E402


def test_get_remaining_audio_for_streaming_updates_accumulated_buffer() -> None:
    recorder = AudioRecorder.__new__(AudioRecorder)
    recorder._data_lock = threading.Lock()
    recorder.chunk_size = 4
    recorder._sample_rate = 4
    recorder._audio_data = [
        np.array([0, 1, 2, 3], dtype=np.float32),
        np.array([4, 5, 6, 7], dtype=np.float32),
        np.array([8, 9, 10, 11], dtype=np.float32),
    ]
    recorder._accumulated_audio = np.concatenate(recorder._audio_data[:2], axis=0).flatten()
    recorder._chunked_samples_sent = len(recorder._accumulated_audio)

    remaining = recorder.get_remaining_audio_for_streaming()

    assert remaining.tolist() == [8.0, 9.0, 10.0, 11.0]
