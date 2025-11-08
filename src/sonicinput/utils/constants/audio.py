"""Audio processing and recording constants"""

# Sample Rates (Hz)
SAMPLE_RATE_16KHZ = 16000  # Whisper standard
SAMPLE_RATE_44KHZ = 44100  # CD quality
SAMPLE_RATE_48KHZ = 48000  # Professional standard

# Audio Format Constants
CHUNK_SIZE_DEFAULT = 1024      # Samples per chunk
CHUNK_SIZE_LARGE = 2048        # For high-quality recording
CHUNK_SIZE_SMALL = 512         # For low-latency

# Audio Conversion
INT16_MAX = 32768.0            # For float conversion: sample / INT16_MAX
INT16_MAX_INT = 32767          # For int conversion: sample * INT16_MAX_INT
INT32_MAX = 2147483648.0       # For 32-bit audio

# Streaming Constants
STREAMING_CHUNK_DURATION_DEFAULT = 30.0  # seconds
STREAMING_CHUNK_DURATION_SHORT = 15.0
STREAMING_CHUNK_DURATION_LONG = 60.0

# Audio Processing
NORMALIZATION_TARGET_LEVEL = 0.8      # Target RMS for normalization
NORMALIZATION_MAX_GAIN = 10.0         # Max gain multiplier
SILENCE_THRESHOLD_DEFAULT = 0.01      # RMS threshold for silence
SILENCE_MIN_DURATION = 0.5            # Min silence duration (seconds)
FRAME_LENGTH_MS = 25                  # Frame length in milliseconds
HOP_LENGTH_MS = 10                    # Hop length in milliseconds

# Audio Level Thresholds
AUDIO_LEVEL_LOW_THRESHOLD = 0.3
AUDIO_LEVEL_MED_THRESHOLD = 0.7
AUDIO_LEVEL_QUIET = 0.0

# Resampling Optimization
RESAMPLE_LARGE_AUDIO_THRESHOLD = 480000  # 30 seconds @ 16kHz
RESAMPLE_CHUNK_SIZE = 240000             # 15 seconds @ 16kHz
RESAMPLE_RATIO_TOLERANCE = 0.01          # Skip if diff < 1%

# Timeouts (seconds)
AUDIO_THREAD_JOIN_TIMEOUT = 1.0
AUDIO_THREAD_JOIN_TIMEOUT_LONG = 2.0
AUDIO_CLEANUP_TIMEOUT = 2.0
