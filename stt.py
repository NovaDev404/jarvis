import re
import time

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

# Audio queue frames are 80 ms.
AUDIO_FRAME = 1280

# Silero VAD uses 30 ms frames at 16 kHz.
VAD_FRAME = 480


# ============================================================
# VAD tuning
# ============================================================

# Speech start threshold.
VAD_THRESHOLD = 0.50

# Lower threshold while already speaking.
# Prevents small fluctuations from cutting speech.
VAD_SILENCE_THRESHOLD = 0.35

# 2 × 30 ms = ~60 ms of confirmed speech.
START_FRAMES = 2

# End after ~650 ms of continuous non-speech.
END_SILENCE_SECONDS = 0.65

# Keep recent audio so the start of speech isn't chopped.
PRE_ROLL_SECONDS = 0.80


# ============================================================
# Limits
# ============================================================

NO_SPEECH_TIMEOUT = 5.0
MAX_DURATION = 15.0


paused = False


def start():
    print("STT ready.")


def stop():
    print("STT stopped.")


def pause():
    global paused
    paused = True


def resume():
    global paused
    paused = False


def flush():
    audio_queue.clear()


def _clean_text(text):
    """
    Remove extra whitespace and an accidentally transcribed
    wake word from the beginning.
    """

    text = " ".join(
        text.split()
    )

    text = re.sub(
        r"^(?:hey\s+)?jarvis[\s,.:;!?-]*",
        "",
        text,
        flags=re.IGNORECASE
    )

    cleaned = text.strip()
    if cleaned:
        print(f"Cleaned text: '{cleaned}'")
    return cleaned


def listen(no_speech_timeout=NO_SPEECH_TIMEOUT):
    print(f"Listening... (timeout: {no_speech_timeout}s)")

    # --------------------------------------------------------
    # Remove stale frames that accumulated while waiting
    # for the wake word.
    #
    # The rolling history remains available for pre-roll.
    # --------------------------------------------------------

    audio_queue.prepare_stt()

    # Reset the VAD's recurrent state.
    vad.reset_states()

    vad_buffer = np.empty(
        0,
        dtype=np.int16
    )

    frames = []

    speech_started = False

    speech_start_count = 0

    silence_samples = 0

    listen_started_at = time.monotonic()

    while True:

        if paused:
            audio_queue.get_stt_chunk(
                timeout=0.1
            )
            continue

        frame = audio_queue.get_stt_chunk(
            timeout=0.1
        )

        if frame is None:
            continue

        was_started = speech_started

        # Add this 80 ms frame to the VAD buffer.
        vad_buffer = np.concatenate(
            (
                vad_buffer,
                frame
            )
        )

        ended = False

        # ----------------------------------------------------
        # Process exact 30 ms VAD frames.
        # ----------------------------------------------------

        while len(vad_buffer) >= VAD_FRAME:

            vad_frame = vad_buffer[
                :VAD_FRAME
            ]

            vad_buffer = vad_buffer[
                VAD_FRAME:
            ]

            score = vad.predict(
                vad_frame,
                frame_size=VAD_FRAME
            )

            # =================================================
            # Waiting for speech
            # =================================================

            if not speech_started:

                if score >= VAD_THRESHOLD:

                    speech_start_count += 1

                else:

                    speech_start_count = 0

                if speech_start_count >= START_FRAMES:

                    speech_started = True

                    # Restore the previous ~800 ms.
                    pre_roll = audio_queue.get_history(
                        PRE_ROLL_SECONDS
                    )

                    if len(pre_roll):

                        frames.append(
                            pre_roll.astype(
                                np.float32
                            ) / 32768.0
                        )

                    silence_samples = 0

            # =================================================
            # Speech already started
            # =================================================

            else:

                if score < VAD_SILENCE_THRESHOLD:

                    silence_samples += VAD_FRAME

                else:

                    silence_samples = 0

                if (
                    silence_samples
                    >= END_SILENCE_SECONDS * RATE
                ):

                    ended = True
                    break

        # ----------------------------------------------------
        # Append the complete audio frame once speech is active.
        #
        # Do not append the frame that contains the transition
        # into speech because the pre-roll already contains it.
        # ----------------------------------------------------

        if speech_started and was_started:

            frames.append(
                frame.astype(
                    np.float32
                ) / 32768.0
            )

        if ended:
            break

        elapsed = (
            time.monotonic()
            - listen_started_at
        )

        # ----------------------------------------------------
        # No speech detected.
        # ----------------------------------------------------

        if (
            not speech_started
            and elapsed >= no_speech_timeout
        ):

            print(f"No speech detected within {no_speech_timeout}s timeout")
            return ""

        # ----------------------------------------------------
        # Prevent an infinite recording.
        # ----------------------------------------------------

        if (
            speech_started
            and elapsed >= MAX_DURATION
        ):

            break

    # ========================================================
    # No usable audio
    # ========================================================

    if not frames:
        print("No frames captured")
        return ""

    audio_data = np.concatenate(
        frames
    )

    duration = (
        len(audio_data)
        / RATE
    )

    if duration < 0.25:
        print(f"Audio too short: {duration:.2f}s")
        return ""

    # ========================================================
    # Whisper
    # ========================================================

    print("Transcribing...")

    segments, info = model.transcribe(
        audio_data,

        language="en",

        # Faster CPU decoding.
        beam_size=1,

        best_of=1,

        temperature=0.0,

        # Each command is independent.
        condition_on_previous_text=False,

        # VAD was already performed above.
        vad_filter=False,

        without_timestamps=True
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )

    return _clean_text(text)
