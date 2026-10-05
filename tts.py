from pathlib import Path
import subprocess
import tempfile
import uuid


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "tts" / "jarvis-medium.onnx"
OUTPUT_DIR = Path(tempfile.gettempdir()) / "jarvis_tts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def speak(text):
    """Generate TTS audio to a temporary WAV file and return its path."""
    text = str(text or "").strip()
    if not text:
        return None

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Piper model not found: {MODEL_PATH}")

    output_path = OUTPUT_DIR / f"jarvis_{uuid.uuid4().hex}.wav"

    subprocess.run(
        [
            "piper",
            "--model",
            str(MODEL_PATH),
            "--output_file",
            str(output_path),
        ],
        input=text,
        text=True,
        check=True,
    )

    return output_path
