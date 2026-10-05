import os
import time

import numpy as np
from openwakeword.model import Model

import audio_queue


class WakeWord:

    def __init__(self, model_path="hey_jarvis_v0.1.tflite"):

        if os.path.exists(model_path):
            self.model = Model(
                wakeword_models=[model_path],
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

        self._debug_last = time.monotonic()

    def wait(self):

        print("Waiting for wake word...")

        while True:

            frame = audio_queue.get_chunk(
                timeout=0.1
            )

            if frame is None:
                continue

            # ------------------------------------------------
            # Temporary audio diagnostics.
            # Prints once every 2 seconds.
            # ------------------------------------------------

            now = time.monotonic()

            if now - self._debug_last >= 2.0:

                self._debug_last = now

                rms = float(
                    np.sqrt(
                        np.mean(
                            frame.astype(
                                np.float32
                            ) ** 2
                        )
                    )
                )

                peak = int(
                    np.max(
                        np.abs(frame)
                    )
                )

                print(
                    f"Wake audio: "
                    f"RMS={rms:.1f} "
                    f"peak={peak}"
                )

            # ------------------------------------------------
            # Wake-word inference
            # ------------------------------------------------

            prediction = self.model.predict(
                frame
            )

            score = prediction[
                self.model_name
            ]

            if (
                not self.triggered
                and score > 0.3
            ):

                self.triggered = True

                print(
                    f"Wake word detected! "
                    f"score={score:.3f}"
                )

                return

            if (
                self.triggered
                and score < 0.2
            ):

                self.triggered = False
