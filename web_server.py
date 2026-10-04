from flask import Flask, render_template
from flask_socketio import SocketIO
import audio_queue
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('audio_data')
def handle_audio(data):
    """Receive raw PCM audio chunk and add to queue."""
    audio_queue.add_pcm_chunk(data)

@socketio.on('sample_rate')
def handle_sample_rate(rate):
    """Receive sample rate from browser."""
    audio_queue.set_sample_rate(rate)

def run_server(host='0.0.0.0', port=5009):
    """Run the Flask-SocketIO server in a separate thread."""
    print(f"WebSocket server started on http://{host}:{port}")
    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)

def start_in_thread(host='0.0.0.0', port=5009):
    """Start the server in a background thread."""
    server_thread = threading.Thread(target=run_server, args=(host, port), daemon=True)
    server_thread.start()
    return server_thread
