import time

import wakeword
import stt
import tts
import web_server


# Start the WebSocket server in a background thread.
web_server.start_in_thread(host="0.0.0.0", port=5009)

ww = wakeword.WakeWord()

# Start the microphone immediately.
# It stays open for the entire lifetime of the program.
stt.start()

try:
    while True:
        # Wait for "Hey Jarvis".
        ww.wait()

        # Microphone is already running, so there is no startup delay.
        text = stt.listen()

        if text:
            print("You:", text)

            # Stop collecting microphone audio while Jarvis prepares TTS.
            stt.pause()

            try:
                audio_path = tts.speak(text)
                if audio_path is not None:
                    web_server.send_tts(audio_path)
            finally:
                # Discard anything captured before/during TTS generation.
                # The browser also stops sending microphone audio while the
                # received TTS audio is actually playing.
                time.sleep(0.05)
                stt.flush()
                stt.resume()

finally:
    stt.stop()
