import math
import queue
import threading
from collections import deque

import numpy as np
from scipy import signal


TARGET_SAMPLE_RATE = 16000
FRAME_SIZE = 1280  # 80 ms at 16 kHz

# Separate queues:
# wake-word detection consumes wake_queue
# STT consumes stt_queue
wake_queue = queue.Queue(maxsize=96)
stt_queue = queue.Queue(maxsize=96)

# Keep the most recent ~2.5 seconds of audio.
# Used to recover the beginning of speech.
_history = deque(maxlen=32)

_source_sample_rate = 16000

# Partial audio waiting to be converted into exact 1280-sample frames.
_audio_buffer = np.empty(0, dtype=np.int16)

_buffer_lock = threading.Lock()


def set_sample_rate(rate):
    global _source_sample_rate

    try:
        rate = int(rate)

        if rate > 0:
            _source_sample_rate = rate

    except (TypeError, ValueError):
        pass


def _push_latest(q, frame):
    """
    Add a frame to a queue.

    If the queue is full, discard the oldest frame so the
    consumers stay close to real time instead of processing
    old microphone audio.
    """

    try:
        q.put_nowait(frame)

    except queue.Full:

        try:
            q.get_nowait()

        except queue.Empty:
            pass

        try:
            q.put_nowait(frame)

        except queue.Full:
            pass


def add_pcm_chunk(pcm_data):
    """
    Receive mono int16 PCM from the browser.

    Converts the incoming stream to 16 kHz if necessary,
    then produces exact 1280-sample frames.

    Every frame is sent to BOTH queues.
    """

    global _audio_buffer

    try:
        if pcm_data is None:
            return

        if not isinstance(
            pcm_data,
            (bytes, bytearray, memoryview)
        ):
            pcm_data = bytes(pcm_data)

        if len(pcm_data) < 2:
            return

        # int16 requires pairs of bytes.
        if len(pcm_data) % 2:
            pcm_data = pcm_data[:-1]

        samples = np.frombuffer(
            pcm_data,
            dtype=np.int16
        )

        if len(samples) == 0:
            return

        source_rate = _source_sample_rate

        # Convert the stream to 16 kHz.
        if source_rate != TARGET_SAMPLE_RATE:

            gcd = math.gcd(
                source_rate,
                TARGET_SAMPLE_RATE
            )

            up = TARGET_SAMPLE_RATE // gcd
            down = source_rate // gcd

            samples = signal.resample_poly(
                samples.astype(np.float32),
                up,
                down
            )

            samples = np.clip(
                samples,
                -32768,
                32767
            ).astype(np.int16)

        with _buffer_lock:

            if len(_audio_buffer) == 0:
                _audio_buffer = samples.copy()

            else:
                _audio_buffer = np.concatenate(
                    (
                        _audio_buffer,
                        samples
                    )
                )

            while len(_audio_buffer) >= FRAME_SIZE:

                frame = _audio_buffer[
                    :FRAME_SIZE
                ].copy()

                _audio_buffer = _audio_buffer[
                    FRAME_SIZE:
                ]

                # Save recent audio for STT pre-roll.
                _history.append(frame)

                # Broadcast to both consumers.
                _push_latest(
                    wake_queue,
                    frame
                )

                _push_latest(
                    stt_queue,
                    frame
                )

    except Exception as e:
        print(f"Audio queue error: {e}")


def get_chunk(timeout=0.1):
    """
    Get a frame for wake-word detection.
    """

    try:
        return wake_queue.get(
            timeout=timeout
        )

    except queue.Empty:
        return None


def get_stt_chunk(timeout=0.1):
    """
    Get a frame for STT.
    """

    try:
        return stt_queue.get(
            timeout=timeout
        )

    except queue.Empty:
        return None


def prepare_stt():
    """
    Remove stale audio that accumulated while the
    wake-word detector was waiting.

    The rolling history is deliberately preserved so
    STT can still use pre-roll.
    """

    while True:

        try:
            stt_queue.get_nowait()

        except queue.Empty:
            break


def get_history(seconds=0.8):
    """
    Return the most recent `seconds` of audio.
    """

    with _buffer_lock:

        if not _history:
            return np.empty(
                0,
                dtype=np.int16
            )

        frames = list(_history)

    audio = np.concatenate(frames)

    samples_needed = max(
        1,
        int(
            seconds *
            TARGET_SAMPLE_RATE
        )
    )

    return audio[
        -samples_needed:
    ].copy()


def clear():
    """
    Completely clear queued audio and history.

    Used after TTS so Jarvis doesn't transcribe
    stale microphone/TTS audio.
    """

    global _audio_buffer

    with _buffer_lock:

        _audio_buffer = np.empty(
            0,
            dtype=np.int16
        )

        _history.clear()

    while True:

        try:
            wake_queue.get_nowait()

        except queue.Empty:
            break

    while True:

        try:
            stt_queue.get_nowait()

        except queue.Empty:
            break
