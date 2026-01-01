"""Whisper-related constants."""


class Whisper:
    """Whisper configuration constants."""

    AVAILABLE_MODELS = [
        "tiny",
        "base",
        "small",
        "medium",
        "large-v3",
        "large-v3-turbo",
        "turbo",
    ]

    LANGUAGE_CODES = {
        "auto": "Automatic Detection",
        "en": "English",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ar": "Arabic",
    }

    COMPUTE_TYPES = ["int8", "int8_float16", "int16", "float16", "float32"]
    DEVICE_TYPES = ["auto", "cpu", "cuda"]
