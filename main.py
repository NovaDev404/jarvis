import time

import wakeword
import stt
import tts
import web_server


# Start the WebSocket server in a background thread
web_server.start_in_thread(host='0.0.0.0', port=5009)

ww = wakeword.WakeWord()

# Start the microphone immediately.
# It stays open for the entire lifetime of the program.
stt.start()

try:
    while True:

        # Wait for "Hey Jarvis"
        ww.wait()

        # Microphone is already running, so there is no startup delay.
        text = stt.listen()

        if text:
            print("You:", text)

            # Stop collecting microphone audio while Jarvis speaks.
            stt.pause()

            try:
                tts.speak(text)

            finally:
                # Give the speaker a tiny moment to finish.
                time.sleep(0.2)

                # Throw away anything that was captured before/during TTS.
                stt.flush()

                # Ready for the next command.
                stt.resume()

finally:
    stt.stop()