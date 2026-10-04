import pyaudio
import numpy as np
from openwakeword.model import Model


class WakeWord:
    def __init__(self, model_path="hey_jarvis_v0.1.tflite"):
        self.model = Model(
            wakeword_models=[model_path],
            inference_framework="tflite"
        )

        self.model_name = list(self.model.models.keys())[0]

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1280
        )

        self.triggered = False

    def wait(self):
        print("Waiting for wake word...")
        """Block until 'Hey Jarvis' is detected."""
        while True:
            data = self.stream.read(1280, exception_on_overflow=False)
            frame = np.frombuffer(data, dtype=np.int16)

            score = self.model.predict(frame)[self.model_name]

            if not self.triggered and score > 0.5:
                self.triggered = True
                return

            if self.triggered and score < 0.2:
                self.triggered = False

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()