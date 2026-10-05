import time
import os
import wakeword
import stt
import ai
import tts
import web_server

web_server.start_in_thread(host="0.0.0.0", port=5009)
ww = wakeword.WakeWord()
stt.start()

try:
    while True:
        ww.wait()
        tts.start()
        stt.flush()
        text = stt.listen()

        if text:
            print("You:", text)
            stt.pause()

            response = ai.prompt(text)
            print("J.A.R.V.I.S: " + response)

            try:
                audio_path = tts.speak(response)
                if audio_path is not None:
                    web_server.send_tts(audio_path)
                    # Clean up the WAV file after sending
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
            finally:
                time.sleep(0.05)
                stt.flush()
                stt.resume()

finally:
    stt.stop()
    tts.stop()