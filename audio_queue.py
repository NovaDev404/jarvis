import queue
import threading
import numpy as np
from scipy import signal


# Shared audio queue for wake word and STT
audio_queue = queue.Queue(maxsize=1000)

# Resampling / framing
TARGET_SAMPLE_RATE = 16000
FRAME_SIZE = 1280  # 80 ms @ 16 kHz

_source_sample_rate = 16000

# Persistent buffer between WebSocket packets
_audio_buffer = np.empty(0, dtype=np.int16)

# Protect buffer because Socket.IO can potentially call handlers concurrently
_buffer_lock = threading.Lock()

_chunk_count = 0
_frame_count = 0


def set_sample_rate(rate):
    """Set the source sample rate from the browser."""
    global _source_sample_rate
    _source_sample_rate = int(rate)


def add_pcm_chunk(pcm_data):
    """
    Add raw PCM chunk (16-bit, mono).

    Incoming audio can be any size/rate.
    It is resampled to 16 kHz and accumulated until
    exactly 1280 samples are available.
    """

    global _audio_buffer
    global _chunk_count
    global _frame_count

    try:
        # Convert raw PCM bytes ? int16 samples
        samples = np.frombuffer(
            pcm_data,
            dtype=np.int16
        )

        if len(samples) == 0:
            return

        source_rate = _source_sample_rate

        # Resample to 16 kHz
        if source_rate != TARGET_SAMPLE_RATE:

            target_length = round(
                len(samples)
                * TARGET_SAMPLE_RATE
                / source_rate
            )

            samples = signal.resample(
                samples.astype(np.float32),
                target_length
            )

            samples = np.clip(
                samples,
                -32768,
                32767
            ).astype(np.int16)

        _chunk_count += 1

        # Add samples to persistent buffer
        with _buffer_lock:

            if len(_audio_buffer) == 0:

                _audio_buffer = samples.copy()

            else:

                _audio_buffer = np.concatenate(
                    (_audio_buffer, samples)
                )

            # Produce complete 1280-sample frames
            while len(_audio_buffer) >= FRAME_SIZE:

                frame = _audio_buffer[:FRAME_SIZE].copy()

                _audio_buffer = _audio_buffer[FRAME_SIZE:]

                _frame_count += 1

                # Queue the exact 1280-sample frame
                try:
                    audio_queue.put_nowait(frame)
                except queue.Full:
                    # Drop oldest frame if queue is full
                    try:
                        audio_queue.get_nowait()
                    except queue.Empty:
                        pass
                    audio_queue.put_nowait(frame)

    except Exception as e:
        pass


def get_chunk(timeout=0.1):
    """Get a complete 1280-sample frame."""

    try:

        return audio_queue.get(
            timeout=timeout
        )

    except queue.Empty:

        return None


def clear():
    """Clear queued audio and partial buffer."""

    global _audio_buffer

    with _buffer_lock:

        _audio_buffer = np.empty(
            0,
            dtype=np.int16
        )

    while True:

        try:
            audio_queue.get_nowait()

        except queue.Empty:

            break