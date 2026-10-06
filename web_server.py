from flask import Flask, render_template, request
from flask_socketio import SocketIO

import audio_queue
import threading
from pathlib import Path
import ssl


app = Flask(__name__, static_folder='static')
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

_last_audio_client_sid = None
_audio_client_lock = threading.Lock()
_tts_finished_event = threading.Event()


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


def send_wake_word_detected(sid=None):
    """Notify the client that the wake word was detected."""
    if sid is None:
        with _audio_client_lock:
            sid = _last_audio_client_sid

    if sid is None:
        return False

    try:
        socketio.emit("wake_word_detected", to=sid)
        return True
    except:
        return False


def send_conversation_start(sid=None):
    """Notify the client that conversation mode has started."""
    if sid is None:
        with _audio_client_lock:
            sid = _last_audio_client_sid

    if sid is None:
        return False

    try:
        socketio.emit("conversation_start", to=sid)
        return True
    except:
        return False


def send_conversation_end(sid=None):
    """Notify the client that conversation mode has ended."""
    if sid is None:
        with _audio_client_lock:
            sid = _last_audio_client_sid

    if sid is None:
        return False

    try:
        socketio.emit("conversation_end", to=sid)
        return True
    except:
        return False


def wait_for_tts_finished(timeout=30):
    """Wait for client to finish playing TTS audio."""
    global _tts_finished_event
    _tts_finished_event.clear()
    return _tts_finished_event.wait(timeout=timeout)


@socketio.on("sample_rate")
def handle_sample_rate(rate):
    """Receive sample rate from browser."""
    global _last_audio_client_sid

    with _audio_client_lock:
        _last_audio_client_sid = request.sid

    audio_queue.set_sample_rate(rate)


@socketio.on("tts_finished")
def handle_tts_finished():
    """Notify server that TTS playback finished on client."""
    global _tts_finished_event
    _tts_finished_event.set()


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


def run_server(host="0.0.0.0", port=5009, use_https=False):
    """Run the Flask-SocketIO server in a separate thread."""
    ssl_context = None

    if use_https:
        cert_path = Path("certs/server.crt")
        key_path = Path("certs/server.key")

        if cert_path.exists() and key_path.exists():
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(str(cert_path), str(key_path))
            print(f"WebSocket server started on https://{host}:{port}")
        else:
            print("SSL certificates not found in certs/, falling back to HTTP")
            print(f"WebSocket server started on http://{host}:{port}")
    else:
        print(f"WebSocket server started on http://{host}:{port}")

    socketio.run(app, host=host, port=port, ssl_context=ssl_context, allow_unsafe_werkzeug=True)


def start_in_thread(host="0.0.0.0", port=5009, use_https=False):
    """Start the server in a background thread."""
    server_thread = threading.Thread(
        target=run_server,
        args=(host, port, use_https),
        daemon=True,
    )
    server_thread.start()
    return server_thread
