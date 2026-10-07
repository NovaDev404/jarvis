from pathlib import Path
import tempfile
import uuid
import subprocess
import threading


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "tts" / "jarvis-medium.onnx"
OUTPUT_DIR = Path(tempfile.gettempdir()) / "jarvis_tts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

piper_process = None
current_output_path = None
loading_thread = None


def start():
    """Start the piper subprocess so the model is loaded and ready for input (fire and forget)."""
    global piper_process, current_output_path, loading_thread
    if piper_process is None and loading_thread is None:
        def load_model():
            global piper_process, current_output_path
            current_output_path = OUTPUT_DIR / f"jarvis_{uuid.uuid4().hex}.wav"
            print("Loading TTS model...")
            piper_process = subprocess.Popen(
                [
                    "piper",
                    "--model", str(MODEL_PATH),
                    "--output_file", str(current_output_path),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print("TTS model loaded.")
        
        loading_thread = threading.Thread(target=load_model, daemon=True)
        loading_thread.start()


def stop():
    """Stop the piper subprocess."""
    global piper_process, current_output_path, loading_thread
    if piper_process is not None:
        piper_process.terminate()
        piper_process = None
        current_output_path = None
    loading_thread = None


def speak(text):
    """Send text to the running piper process and wait for it to generate audio."""
    global piper_process, current_output_path, loading_thread

    text = str(text or "").strip()
    if not text:
        return None

    # Wait for the initial load to complete if still loading
    if loading_thread is not None:
        loading_thread.join()
        loading_thread = None

    if piper_process is None:
        raise RuntimeError("TTS model not loaded. Call start() first.")

    # Send text to the running piper process
    piper_process.stdin.write(text + "\n")
    piper_process.stdin.flush()

    # Close stdin to send EOF signal - piper will process and exit
    piper_process.stdin.close()

    # Wait for piper to finish
    piper_process.wait()

    # Clear the process reference (caller must call start() again for next utterance)
    piper_process = None

    return current_output_path
