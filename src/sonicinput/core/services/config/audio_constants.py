"""Audio-related constants."""


class Audio:
    """Audio configuration constants."""

    SAMPLE_RATES = [8000, 16000, 22050, 44100, 48000]
    SUPPORTED_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]

    MIN_RECORDING_DURATION = 0.5
    MAX_RECORDING_DURATION = 300

    SILENCE_THRESHOLD = 0.01
    NOISE_GATE_THRESHOLD = 0.005

    WAVEFORM_SAMPLES = 100
    WAVEFORM_UPDATE_INTERVAL = 50
