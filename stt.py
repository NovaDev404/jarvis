import queue
import numpy as np
from faster_whisper import WhisperModel
import audio_queue


model = WhisperModel(
    "distil-small.en",
    device="cpu",
    compute_type="int8"
)

RATE = 16000
CHUNK = 1280  # 80ms (matches wake word chunk size)

SILENCE_THRESHOLD = 0.007  # Lowered to catch quieter speech
SILENCE_DURATION = 1.5  # Increased to allow for natural pauses in speech
MAX_DURATION = 15

paused = False


def start():
    print("STT ready (using WebSocket audio stream).")


def stop():
    print("STT stopped.")


def pause():
    global paused
    paused = True


def resume():
    global paused
    paused = False


def flush():
    """Discard audio captured before listening again."""
    audio_queue.clear()


def listen():
    print("Listening...")

    frames = []
    started = False
    silent_time = 0.0
    total_time = 0.0
    chunk_count = 0

    while total_time < MAX_DURATION:
        # Don't collect audio while TTS is playing
        if paused:
            audio_queue.get_chunk(timeout=0.1)
            continue

        # Wait for the next chunk of audio from WebSocket
        audio = audio_queue.get_chunk(timeout=0.1)
        if audio is None:
            continue

        chunk_count += 1

        # Convert int16 to float32 for whisper
        audio_float = audio.astype(np.float32) / 32768.0
        frames.append(audio_float)

        volume = np.sqrt(np.mean(audio_float ** 2))

        # Debug: print volume every 50 chunks
        if chunk_count % 50 == 0:
            print(f"STT: chunk {chunk_count}, volume={volume:.4f}, started={started}, silent_time={silent_time:.2f}s")

        if volume > SILENCE_THRESHOLD:
            if not started:
                print(f"STT: speech started at chunk {chunk_count}, volume={volume:.4f}")
            started = True
            silent_time = 0.0

        elif started:
            silent_time += CHUNK / RATE
            if chunk_count % 50 == 0:
                print(f"STT: silence accumulating, silent_time={silent_time:.2f}s")

        total_time += CHUNK / RATE

        # Stop after speech has ended.
        if started and silent_time >= SILENCE_DURATION:
            print(f"STT: silence detected after {silent_time:.2f}s, stopping. Total frames: {len(frames)}")
            break

    if not frames:
        print("STT: no frames collected")
        return ""

    audio_data = np.concatenate(frames)
    print(f"STT: transcribing {len(audio_data)} samples ({len(audio_data)/16000:.2f}s)...")

    segments, info = model.transcribe(
        audio_data,
        beam_size=5
    )

    text = "".join(
        segment.text
        for segment in segments
    ).strip()

    return text