import subprocess

def speak(text):
    subprocess.run(
        'echo "' + text + '" | piper --model tts/jarvis-medium.onnx',
        shell=True,
        check=True
    )