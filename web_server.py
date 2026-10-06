from flask import Flask, render_template, request
from flask_socketio import SocketIO

import audio_queue
import threading
from pathlib import Path
import ssl
import uuid
import ai


app = Flask(__name__, static_folder='static')
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

_last_audio_client_sid = None
_audio_client_lock = threading.Lock()
_tts_finished_event = threading.Event()

# Text-only mode conversation storage
_text_conversations = {}  # {conversation_id: {"history": [], "sid": client_sid}}
_text_conversations_lock = threading.Lock()

# Pending confirmations
_pending_confirmations = {}  # {request_id: {"event": threading.Event(), "result": None}}
_pending_confirmations_lock = threading.Lock()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/memory")
def get_memory():
    """API endpoint to get current memory content."""
    try:
        with open("memory.txt", "r") as f:
            memory_content = f.read()
        return {"content": memory_content}
    except FileNotFoundError:
        return {"content": ""}


@app.route("/api/memory", methods=["POST"])
def save_memory():
    """API endpoint to save memory content."""
    data = request.get_json()
    content = data.get("content", "")
    
    try:
        with open("memory.txt", "w") as f:
            f.write(content)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


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

    # Clear text-only conversation for this client
    with _text_conversations_lock:
        conv_id_to_remove = None
        for conv_id, conv_data in _text_conversations.items():
            if conv_data.get("sid") == request.sid:
                conv_id_to_remove = conv_id
                break
        if conv_id_to_remove:
            del _text_conversations[conv_id_to_remove]
            print(f"Text-only conversation {conv_id_to_remove} cleared due to disconnect")


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


# ============================================================
# Text-only WebSocket handlers
# ============================================================

@socketio.on("text_connect")
def handle_text_connect():
    """Client connects in text-only mode, generates conversation ID."""
    conversation_id = str(uuid.uuid4())
    
    with _text_conversations_lock:
        _text_conversations[conversation_id] = {
            "history": [],
            "sid": request.sid
        }
    
    socketio.emit("text_connected", {"conversation_id": conversation_id}, to=request.sid)
    print(f"Text-only client connected with conversation ID: {conversation_id}")


@socketio.on("text_message")
def handle_text_message(data):
    """Receive text message from client, process with AI, and send response."""
    conversation_id = data.get("conversation_id")
    user_message = data.get("message")

    if not conversation_id or not user_message:
        socketio.emit("text_error", {"error": "Missing conversation_id or message"}, to=request.sid)
        return

    with _text_conversations_lock:
        if conversation_id not in _text_conversations:
            socketio.emit("text_error", {"error": "Invalid conversation ID"}, to=request.sid)
            return

        # Update SID in case of reconnection
        _text_conversations[conversation_id]["sid"] = request.sid
        conversation_history = _text_conversations[conversation_id]["history"]

    try:
        # Get AI response (tools still work, with text mode confirmation)
        response = ai.prompt(user_message, conversation_history, text_mode=True, conversation_id=conversation_id)

        # Update conversation history
        with _text_conversations_lock:
            _text_conversations[conversation_id]["history"].append({
                "role": "user",
                "content": user_message
            })
            _text_conversations[conversation_id]["history"].append({
                "role": "assistant",
                "content": response
            })

        # Send response back to client
        socketio.emit("text_response", {
            "message": response,
            "conversation_id": conversation_id
        }, to=request.sid)

    except Exception as e:
        socketio.emit("text_error", {"error": str(e)}, to=request.sid)


@socketio.on("text_clear")
def handle_text_clear(data):
    """Clear conversation history for a given conversation ID."""
    conversation_id = data.get("conversation_id")

    if not conversation_id:
        socketio.emit("text_error", {"error": "Missing conversation_id"}, to=request.sid)
        return

    with _text_conversations_lock:
        if conversation_id in _text_conversations:
            _text_conversations[conversation_id]["history"] = []
            socketio.emit("text_cleared", {"conversation_id": conversation_id}, to=request.sid)
        else:
            socketio.emit("text_error", {"error": "Invalid conversation ID"}, to=request.sid)


def request_text_confirmation(action_description, conversation_id):
    """Request confirmation from text-mode client and wait for response."""
    import uuid
    request_id = str(uuid.uuid4())
    event = threading.Event()

    # Store the pending confirmation
    with _pending_confirmations_lock:
        _pending_confirmations[request_id] = {
            "event": event,
            "result": None
        }

    # Get the client SID for this conversation
    with _text_conversations_lock:
        if conversation_id not in _text_conversations:
            with _pending_confirmations_lock:
                del _pending_confirmations[request_id]
            return None
        client_sid = _text_conversations[conversation_id]["sid"]

    # Send confirmation request to client
    try:
        socketio.emit("confirmation_request", {
            "request_id": request_id,
            "action_description": action_description
        }, to=client_sid)

        # Wait for response (30 second timeout)
        if event.wait(timeout=30):
            with _pending_confirmations_lock:
                result = _pending_confirmations[request_id]["result"]
                del _pending_confirmations[request_id]
            return result
        else:
            # Timeout
            with _pending_confirmations_lock:
                if request_id in _pending_confirmations:
                    del _pending_confirmations[request_id]
            return None
    except Exception as e:
        print(f"Error requesting confirmation: {e}")
        with _pending_confirmations_lock:
            if request_id in _pending_confirmations:
                del _pending_confirmations[request_id]
        return None


@socketio.on("confirmation_response")
def handle_confirmation_response(data):
    """Handle confirmation response from client."""
    request_id = data.get("request_id")
    confirmed = data.get("confirmed")

    if not request_id or confirmed is None:
        return

    with _pending_confirmations_lock:
        if request_id in _pending_confirmations:
            _pending_confirmations[request_id]["result"] = confirmed
            _pending_confirmations[request_id]["event"].set()


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
