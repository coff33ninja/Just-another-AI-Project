#!/usr/bin/env python3
"""
Try multiple speech_recognition microphone indices to find a working one
"""
import speech_recognition as sr
import numpy as np

candidates = [1,2,11,12,24,29,35,22]

print('Available microphones (enumeration may show many duplicates):')
for i, n in enumerate(sr.Microphone.list_microphone_names()):
    if i in candidates:
        print(f'  [{i}] {n}')

for idx in candidates:
    print('\n' + '='*60)
    print(f'Testing index {idx}...')
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = False
    try:
        with sr.Microphone(device_index=idx) as source:
            print('  Adjusting for ambient noise (1s)...')
            r.adjust_for_ambient_noise(source, duration=1)
            print('  Energy threshold:', r.energy_threshold)
            print('  Say something now (3s)...')
            audio = r.listen(source, timeout=4, phrase_time_limit=3)
            print('  Captured audio size:', len(audio.get_wav_data()))
            audio_data = np.frombuffer(audio.get_wav_data(), dtype=np.int16)
            rms = np.sqrt(np.mean(audio_data**2))
            print('  RMS:', int(rms))
            try:
                text = r.recognize_google(audio)
                print('  Google heard:', text)
            except Exception as e:
                print('  Google STT error:', e)
            print('\n✓ Index', idx, 'works')
    except Exception as e:
        print('  ✗ Index', idx, 'failed:', e)

print('\nDone')
