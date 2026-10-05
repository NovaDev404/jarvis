from flask import Flask, render_template, request
from flask_socketio import SocketIO

import audio_queue
import threading
from pathlib import Path


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

_last_audio_client_sid = None
_audio_client_lock = threading.Lock()


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("audio_data")
def handle_audio(data):
    """Receive raw PCM audio chunk and add to queue."""
    global _last_audio_client_sid

    with _audio_client_lock:
        _last_audio_client_sid = request.sid

    audio_queue.add_pcm_chunk(data)


@socketio.on("sample_rate")
def handle_sample_rate(rate):
    """Receive sample rate from browser."""
    global _last_audio_client_sid

    with _audio_client_lock:
        _last_audio_client_sid = request.sid

    audio_queue.set_sample_rate(rate)


@socketio.on("disconnect")
def handle_disconnect():
    """Forget the client when it disconnects."""
    global _last_audio_client_sid

    with _audio_client_lock:
        if _last_audio_client_sid == request.sid:
            _last_audio_client_sid = None


def send_tts(audio_path, sid=None):
    """Send a generated WAV file to the client that supplied the microphone."""
    path = Path(audio_path)

    if not path.is_file():
        raise FileNotFoundError(f"TTS audio file not found: {path}")

    if sid is None:
        with _audio_client_lock:
            sid = _last_audio_client_sid

    if sid is None:
        path.unlink(missing_ok=True)
        return False

    try:
        with path.open("rb") as audio_file:
            audio_bytes = audio_file.read()

        socketio.emit("tts_audio", audio_bytes, to=sid)
        return True
    finally:
        path.unlink(missing_ok=True)


def run_server(host="0.0.0.0", port=5009):
    """Run the Flask-SocketIO server in a separate thread."""
    print(f"WebSocket server started on http://{host}:{port}")
    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)


def start_in_thread(host="0.0.0.0", port=5009):
    """Start the server in a background thread."""
    server_thread = threading.Thread(
        target=run_server,
        args=(host, port),
        daemon=True,
    )
    server_thread.start()
    return server_thread
