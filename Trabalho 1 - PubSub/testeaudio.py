import sounddevice as sd
import numpy as np

duration = 2  # segundos
print("Gravando...")
audio = sd.rec(int(duration * 44100), samplerate=44100, channels=1, dtype='int16')
sd.wait()
print("Reproduzindo...")
sd.play(audio, samplerate=44100)
sd.wait()
