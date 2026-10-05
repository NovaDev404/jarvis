import os

from openwakeword.model import Model

import audio_queue


class WakeWord:

    def __init__(
        self,
        model_path="hey_jarvis_v0.1.tflite"
    ):

        if os.path.exists(model_path):

            self.model = Model(
                wakeword_models=[
                    model_path
                ],
                inference_framework="tflite"
            )

        else:

            self.model = Model(
                inference_framework="tflite"
            )

        self.model_name = list(
            self.model.models.keys()
        )[0]

        self.triggered = False

    def wait(self):

        print(
            "Waiting for wake word..."
        )

        while True:

            frame = audio_queue.get_chunk(
                timeout=0.1
            )

            if frame is None:
                continue

            prediction = self.model.predict(
                frame
            )

            score = prediction[
                self.model_name
            ]

            if (
                not self.triggered
                and score > 0.4
            ):

                self.triggered = True

                print(
                    "Wake word detected!"
                )

                return

            if (
                self.triggered
                and score < 0.2
            ):

                self.triggered = False
