"""
Cloud Chunk Accumulator - Buffer and transcribe audio chunks for cloud providers.

This module implements chunked streaming transcription for cloud providers (Groq, SiliconFlow, Qwen)
to avoid rate limits on long recordings by sending audio in periodic chunks during recording.
"""

import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import numpy as np

from ..utils.logger import app_logger

if TYPE_CHECKING:
    from ..core.interfaces.speech import ISpeechService


class CloudChunkAccumulator:
    """
    Accumulate audio chunks and trigger cloud transcription at intervals.

    This class buffers incoming audio data and triggers asynchronous transcription
    when the buffer duration reaches the configured chunk duration threshold.
    Results from all chunks are combined in order when requested.
    """

    def __init__(
        self,
        speech_service: "ISpeechService",
        chunk_duration: float = 15.0,
        sample_rate: int = 16000,
    ):
        """
        Initialize the cloud chunk accumulator.

        Args:
            speech_service: The speech service to use for transcription
            chunk_duration: Duration in seconds for each chunk (default: 15.0)
            sample_rate: Audio sample rate in Hz (default: 16000)
        """
        self._speech_service = speech_service
        self._chunk_duration = chunk_duration
        self._sample_rate = sample_rate

        # Buffering state
        self._buffer: List[np.ndarray] = []
        self._buffer_duration = 0.0

        # Chunk tracking
        self._chunks: List[Tuple[int, Future]] = []
        self._chunk_counter = 0

        # Thread pool for async transcription (max 3 concurrent chunks)
        self._executor = ThreadPoolExecutor(max_workers=3)

        app_logger.log_audio_event(
            "CloudChunkAccumulator initialized",
            {
                "chunk_duration": chunk_duration,
                "sample_rate": sample_rate,
                "max_workers": 3,
            },
        )

    def add_audio(self, audio_data: np.ndarray) -> None:
        """
        Add audio data and immediately trigger transcription.

        Since AudioRecorder already handles chunking at the configured interval,
        we flush each chunk immediately instead of accumulating.

        Args:
            audio_data: Audio samples as numpy array (already chunked by AudioRecorder)
        """
        # Add to buffer
        self._buffer.append(audio_data)
        self._buffer_duration += len(audio_data) / self._sample_rate

        # Immediately flush this chunk for transcription
        # (AudioRecorder already handles the chunking interval)
        self._flush_chunk()

    def _flush_chunk(self) -> None:
        """
        Flush current buffer as a chunk and start async transcription.

        Combines buffered audio into a single chunk, assigns a chunk ID,
        and submits to thread pool for asynchronous transcription.
        """
        if not self._buffer:
            return

        # Combine buffer into single chunk
        chunk_audio = np.concatenate(self._buffer)
        chunk_id = self._chunk_counter
        self._chunk_counter += 1

        app_logger.log_audio_event(
            "Flushing audio chunk for transcription",
            {
                "chunk_id": chunk_id,
                "duration": self._buffer_duration,
                "samples": len(chunk_audio),
            },
        )

        # Submit async transcription
        future = self._executor.submit(self._transcribe_chunk, chunk_id, chunk_audio)
        self._chunks.append((chunk_id, future))

        # Reset buffer
        self._buffer = []
        self._buffer_duration = 0.0

    def _transcribe_chunk(
        self, chunk_id: int, audio_data: np.ndarray
    ) -> Tuple[int, str]:
        """
        Transcribe a single chunk (runs in thread pool).

        Implements retry logic with exponential backoff for transient failures.

        Args:
            chunk_id: Unique identifier for this chunk
            audio_data: Audio samples to transcribe

        Returns:
            Tuple of (chunk_id, transcribed_text)

        Raises:
            Exception: If all retry attempts fail
        """
        max_retries = 3
        retry_delay = 1.0  # Initial delay in seconds

        for attempt in range(max_retries):
            try:
                result = self._speech_service.transcribe(audio_data)
                text = result.get("text", "")

                app_logger.log_audio_event(
                    "Cloud chunk transcription completed",
                    {
                        "chunk_id": chunk_id,
                        "attempt": attempt + 1,
                        "text_length": len(text),
                        "text_preview": text[:50] if text else "",
                    },
                )
                return (chunk_id, text)

            except Exception as e:
                is_last_attempt = attempt == max_retries - 1

                if is_last_attempt:
                    app_logger.log_error(
                        e,
                        f"cloud_chunk_transcription_{chunk_id}_failed_all_retries",
                    )
                    raise
                else:
                    wait_time = retry_delay * (2**attempt)
                    app_logger.log_audio_event(
                        "Cloud chunk transcription failed, retrying",
                        {
                            "chunk_id": chunk_id,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "wait_time": wait_time,
                            "error": str(e),
                        },
                    )
                    time.sleep(wait_time)

        # Should never reach here due to raise in last attempt
        return (chunk_id, "")

    def get_results(self, timeout: float = 30.0) -> Dict[str, Any]:
        """
        Wait for all chunks to complete and combine results.

        Flushes any remaining buffered audio, waits for all chunk transcriptions
        to complete (with timeout), and combines the results in order.

        Args:
            timeout: Maximum wait time in seconds for each chunk

        Returns:
            Dictionary with keys:
                - text: Combined transcription text from all successful chunks
                - stats: Statistics about chunk processing
        """
        # Flush any remaining audio
        self._flush_chunk()

        # Wait for all futures and collect results
        results: List[Tuple[int, str]] = []
        failed_chunks: List[int] = []

        for chunk_id, future in self._chunks:
            try:
                chunk_result = future.result(timeout=timeout)
                results.append(chunk_result)
            except TimeoutError:
                app_logger.log_audio_event(
                    "Cloud chunk transcription timeout",
                    {"chunk_id": chunk_id, "timeout": timeout},
                )
                failed_chunks.append(chunk_id)
            except Exception as e:
                app_logger.log_error(
                    e,
                    f"cloud_chunk_{chunk_id}_transcription_failed",
                )
                failed_chunks.append(chunk_id)

        # Sort by chunk_id and combine text
        results.sort(key=lambda x: x[0])
        combined_text = " ".join(text for _, text in results)

        stats = {
            "total_chunks": self._chunk_counter,
            "successful_chunks": len(results),
            "failed_chunks": len(failed_chunks),
            "failed_chunk_ids": failed_chunks,
            "streaming_mode": "chunked",
        }

        app_logger.log_audio_event(
            "Cloud chunk accumulator results combined",
            {
                "total_chunks": stats["total_chunks"],
                "successful": stats["successful_chunks"],
                "failed": stats["failed_chunks"],
                "text_length": len(combined_text),
            },
        )

        return {"text": combined_text, "stats": stats}

    def shutdown(self) -> None:
        """
        Shutdown the thread pool executor.

        Should be called when the accumulator is no longer needed to clean up resources.
        """
        self._executor.shutdown(wait=True)
        app_logger.log_audio_event("CloudChunkAccumulator shutdown", {})
