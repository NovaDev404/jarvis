import time
import re

import numpy as np
from faster_whisper import WhisperModel
from openwakeword.vad import VAD

import audio_queue


# ============================================================
# Whisper
# ============================================================

model = WhisperModel(
    "distil-small.en",
    device="cpu",
    compute_type="int8"
)


# ============================================================
# Silero VAD
# ============================================================

vad = VAD(
    n_threads=1
)


# ============================================================
# Audio
# ============================================================

RATE = 16000

# audio_queue gives us 1280 samples = 80 ms
CHUNK = 1280

# Silero VAD processes 30 ms frames.
VAD_CHUNK = 480


# ============================================================
# Speech detection tuning
# ============================================================

# VAD probability required to consider audio speech.
VAD_THRESHOLD = 0.50

# Once speech has started, this lower threshold prevents
# tiny dips in VAD confidence from chopping the sentence.
VAD_SILENCE_THRESHOLD = 0.35

# Require 2 consecutive VAD frames (~60 ms) before
# declaring that the user has started speaking.
START_FRAMES = 2

# End the utterance after this much continuous silence.
#
# 650 ms = 0.65 seconds.
END_SILENCE = 0.65

# Audio immediately before speech starts.
#
# This is important because wake-word detection and the
# transition into STT can otherwise eat the beginning of
# "what's the weather..."
PRE_ROLL = 0.8


# ============================================================
# Safety limits
# ============================================================

NO_SPEECH_TIMEOUT = 5.0
MAX_DURATION = 15.0


paused = False


# ============================================================
# Lifecycle
# ============================================================

def start():
    print("STT ready (distil-small.en + Silero VAD).")


def stop():
    print("STT stopped.")


def pause():
    global paused
    paused = True


def resume():
    global paused
    paused = False


def flush():
    """
    Throw away audio after TTS.

    This prevents Jarvis from transcribing its own response.
    """
    audio_queue.clear()


# ============================================================
# Text cleanup
# ============================================================

def clean_text(text):
    text = " ".join(text.split())

    # The pre-roll may contain the wake word.
    # Remove it if Whisper picked it up.
    text = re.sub(
        r"^(?:hey\s+)?jarvis[\s,.:;!?-]*",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


# ============================================================
# Listen
# ============================================================

def listen():

    print("Listening...")

    # --------------------------------------------------------
    # Important:
    #
    # WakeWord consumes wake_queue, NOT stt_queue.
    #
    # The STT queue has therefore been collecting audio while
    # we were waiting for "Hey Jarvis".
    #
    # Discard that stale queue, but KEEP the rolling history.
    # --------------------------------------------------------

    audio_queue.prepare_stt()

    # Reset Silero's internal state.
    vad.reset_states()

    vad_buffer = np.empty(
        0,
        dtype=np.int16
    )

    frames = []

    speech_started = False

    speech_start_count = 0

    silent_samples = 0

    start_time = time.monotonic()

    # --------------------------------------------------------
    # Main audio loop
    # --------------------------------------------------------

    while True:

        if paused:

            audio_queue.get_stt_chunk(
                timeout=0.1
            )

            continue

        audio = audio_queue.get_stt_chunk(
            timeout=0.1
        )

        if audio is None:
            continue

        # Add 80 ms to VAD buffer.
        vad_buffer = np.concatenate(
            (
                vad_buffer,
                audio
            )
        )

        # ----------------------------------------------------
        # Process exact 30 ms VAD frames.
        # ----------------------------------------------------

        while len(vad_buffer) >= VAD_CHUNK:

            vad_audio = vad_buffer[:VAD_CHUNK]

            vad_buffer = vad_buffer[VAD_CHUNK:]

            # Silero VAD score.
            score = vad.predict(
                vad_audio,
                frame_size=VAD_CHUNK
            )

            # =================================================
            # Waiting for speech
            # =================================================

            if not speech_started:

                if score >= VAD_THRESHOLD:

                    speech_start_count += 1

                else:

                    speech_start_count = 0

                # ~60 ms of confirmed speech.
                if speech_start_count >= START_FRAMES:

                    speech_started = True

                    print(
                        f"STT: speech started "
                        f"(VAD={score:.3f})"
                    )

                    # ------------------------------------------------
                    # IMPORTANT:
                    #
                    # Grab audio immediately before speech started.
                    # This prevents the first syllable from disappearing.
                    # ------------------------------------------------

                    history = audio_queue.get_history(
                        PRE_ROLL
                    )

                    if len(history):

                        frames.append(
                            history.astype(
                                np.float32
                            ) / 32768.0
                        )

                    silent_samples = 0

            # =================================================
            # Already speaking
            # =================================================

            else:

                if score < VAD_SILENCE_THRESHOLD:

                    silent_samples += VAD_CHUNK

                else:

                    silent_samples = 0

                # ------------------------------------------------
                # End of speech.
                # ------------------------------------------------

                if (
                    silent_samples
                    >= END_SILENCE * RATE
                ):

                    print(
                        f"STT: speech ended "
                        f"after "
                        f"{silent_samples / RATE:.2f}s silence"
                    )

                    break

        # ----------------------------------------------------
        # Once speech has started, store this entire 80 ms
        # audio frame.
        # ----------------------------------------------------

        if speech_started:

            frames.append(
                audio.astype(
                    np.float32
                ) / 32768.0
            )

        # ----------------------------------------------------
        # Don't wait forever for someone to speak.
        # ----------------------------------------------------

        elapsed = (
            time.monotonic()
            - start_time
        )

        if (
            not speech_started
            and elapsed >= NO_SPEECH_TIMEOUT
        ):

            print(
                "STT: no speech detected."
            )

            return ""

        # ----------------------------------------------------
        # Maximum utterance length.
        # ----------------------------------------------------

        if (
            speech_started
            and elapsed >= MAX_DURATION
        ):

            print(
                "STT: maximum utterance duration reached."
            )

            break

        # ----------------------------------------------------
        # The VAD loop can have detected the end.
        # Check it here.
        # ----------------------------------------------------

        if (
            speech_started
            and silent_samples
            >= END_SILENCE * RATE
        ):

            break

    # ========================================================
    # Nothing recorded
    # ========================================================

    if not frames:

        print(
            "STT: no audio captured."
        )

        return ""

    audio_data = np.concatenate(
        frames
    )

    duration = (
        len(audio_data)
        / RATE
    )

    print(
        f"STT: transcribing "
        f"{duration:.2f}s..."
    )

    # Don't send microscopic clips to Whisper.
    if duration < 0.25:

        print(
            "STT: utterance too short."
        )

        return ""

    # ========================================================
    # Whisper
    # ========================================================

    segments, info = model.transcribe(

        audio_data,

        language="en",

        # Faster than your current beam_size=5.
        beam_size=1,

        best_of=1,

        temperature=0.0,

        # Every command is a fresh utterance.
        # Prevents previous speech from influencing this one.
        condition_on_previous_text=False,

        # VAD has already been done above.
        vad_filter=False,

        without_timestamps=True
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )

    text = clean_text(text)

    print(
        f"STT result: {text!r}"
    )

    return text
