# J.A.R.V.I.S.

The server for a voice-controlled AI assistant that listens, processes, and responds like Tony Stark's AI assistant, J.A.R.V.I.S., from the MCU.

## Speed

On average, J.A.R.V.I.S. responds in about four seconds on CPU after the user finishes talking.

## How It Works

1. **Wake Word Detection** - Streams microphone over websocket to server, and listens continuously for "Hey Jarvis" using OpenWakeWord
2. **Speech-to-Text** - Transcribes your voice input using Faster Whisper with Whisper Distil, and Silero VAD
3. **AI Processing** - Generates near-instant responses using Groq and a J.A.R.V.I.S. optimised system prompt
4. **Text-to-Speech** - Send the response from Piper TTS to client

## Technologies

- **OpenWakeWord** - Wake word detection using `hey_jarvis_v0.1.tflite`
- **Faster Whisper** - Speech recognition using `distil-small.en`
- **Silero VAD** - Voice activity detection
- **Groq** - AI inference using `qwen3.8-27b`
- **Piper** - Neural text-to-speech using `jarvis-medium.onnx`
