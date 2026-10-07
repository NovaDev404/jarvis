import time
import wakeword
import stt
import ai
import tts
import web_server
import argparse

parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Voice Assistant")
parser.add_argument("--https", action="store_true", help="Enable HTTPS with SSL certificates from certs/")
args = parser.parse_args()

web_server.start_in_thread(host="0.0.0.0", port=5009, use_https=args.https)
ww = wakeword.WakeWord()

# Conversation listening timeout (seconds)
CONVERSATION_TIMEOUT = 5.0

try:
    while True:
        # Wait for wake word
        ww.wait()
        web_server.send_wake_word_detected()
        overall_start = time.time()
        print("[TIMING] Wake word detected")

        # Start TTS immediately after wake word
        tts.start()
        tts_start_elapsed = time.time() - overall_start
        print(f"[TIMING] TTS started in {tts_start_elapsed:.2f}s")

        # Start conversation mode
        conversation_history = []
        web_server.send_conversation_start()

        text = None
        while True:
            # If we don't have text, listen for it
            if text is None:
                stt.flush()
                # Start timing when STT begins listening
                turn_start = time.time()
                text = stt.listen()

            if text:
                print("You:", text)

                # Get AI response with conversation history
                response = ai.prompt(text, conversation_history)
                print("J.A.R.V.I.S:", response)

                # Add to conversation history
                conversation_history.append({"role": "user", "content": text})
                conversation_history.append({"role": "assistant", "content": response})

                audio_path = tts.speak(response)
                if audio_path is not None:
                    web_server.send_tts(audio_path)
                    tts_speak_elapsed = time.time() - turn_start
                    print(f"[TIMING] TTS audio sent to client in {tts_speak_elapsed:.2f}s")
                    # Wait for client to finish playing audio
                    web_server.wait_for_tts_finished()
                
                # Restart TTS for next response
                tts.start()
                time.sleep(0.05)
                stt.flush()

                # Listen for follow-up with 5-second timeout
                print("Listening for follow-up...")
                stt.flush()
                # Reset timing for follow-up STT
                turn_start = time.time()
                follow_up = stt.listen(no_speech_timeout=CONVERSATION_TIMEOUT)
                print(f"Follow-up received: '{follow_up}'")

                if follow_up and follow_up.strip():
                    # Process follow-up in next iteration
                    text = follow_up
                else:
                    # No follow-up, end conversation
                    print("Conversation ended - returning to wake word")
                    break
            else:
                # No speech detected, end conversation
                print("No speech detected - returning to wake word")
                break

        # Clear conversation history and go back to wake word
        conversation_history = []
        web_server.send_conversation_end()
        
        # Stop TTS when returning to wake word
        tts.stop()

finally:
    tts.stop()