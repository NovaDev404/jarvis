import queue

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


model = WhisperModel(
    "distil-small.en",
    device="cpu",
    compute_type="int8"
)

RATE = 16000
CHUNK = 1600  # 100 ms

SILENCE_THRESHOLD = 0.015
SILENCE_DURATION = 0.8
MAX_DURATION = 15


audio_queue = queue.Queue()
stream = None
paused = False


def _callback(indata, frames, time_info, status):
    if status:
        print("Audio:", status)

    # Don't collect audio while TTS is playing.
    if not paused:
        audio_queue.put(indata[:, 0].copy())


def start():
    global stream

    if stream is not None:
        return

    print("Starting STT microphone...")

    stream = sd.InputStream(
        samplerate=RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK,
        callback=_callback
    )

    stream.start()

    print("STT microphone ready.")


def stop():
    global stream

    if stream is not None:
        stream.stop()
        stream.close()
        stream = None


def pause():
    global paused
    paused = True


def resume():
    global paused
    paused = False


def flush():
    """Discard audio captured before listening again."""
    while True:
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break


def listen():
    print("Listening...")

    frames = []
    started = False
    silent_time = 0.0
    total_time = 0.0

    while total_time < MAX_DURATION:

        # Wait for the next chunk of microphone audio.
        audio = audio_queue.get()

        frames.append(audio)

        volume = np.sqrt(np.mean(audio ** 2))

        if volume > SILENCE_THRESHOLD:
            started = True
            silent_time = 0.0

        elif started:
            silent_time += CHUNK / RATE

        total_time += CHUNK / RATE

        # Stop after speech has ended.
        if started and silent_time >= SILENCE_DURATION:
            break

    if not frames:
        return ""

    audio_data = np.concatenate(frames)

    print("Transcribing...")

    segments, info = model.transcribe(
        audio_data,
        beam_size=5
    )

    text = "".join(
        segment.text
        for segment in segments
    ).strip()

    return text