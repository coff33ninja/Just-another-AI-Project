#!/usr/bin/env python3
"""
Test speech_recognition Microphone at index from MICROPHONE_INDEX env var
"""
import os
import time
from dotenv import load_dotenv
load_dotenv()
import speech_recognition as sr
import numpy as np

mic_index = os.getenv('MICROPHONE_INDEX')
if mic_index is None or mic_index == '':
    print('MICROPHONE_INDEX not set in .env')
    exit(1)

mic_index = int(mic_index)
print(f'Testing sr.Microphone index: {mic_index}')

print('\nAvailable microphones:')
for i, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f'  [{i}] {name}')

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = False

try:
    with sr.Microphone(device_index=mic_index) as source:
        print('\nAdjusting for ambient noise (2s)...')
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f'Energy threshold now: {recognizer.energy_threshold}')
        print('\nPlease say something (5s)...')
        audio = recognizer.listen(source, timeout=6, phrase_time_limit=5)
        print('Captured audio, size:', len(audio.get_wav_data()))
        audio_data = np.frombuffer(audio.get_wav_data(), dtype=np.int16)
        rms = np.sqrt(np.mean(audio_data**2))
        print('Signal RMS:', int(rms))

        try:
            text = recognizer.recognize_google(audio)
            print('Google STT heard:', text)
        except Exception as e:
            print('Google STT error:', e)

except Exception as e:
    print('Error using microphone index:', e)
    import traceback
    traceback.print_exc()
