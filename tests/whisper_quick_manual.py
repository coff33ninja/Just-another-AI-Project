"""
Manual Whisper test script

Usage:
  - Run directly from the project root:
      python tests/whisper_quick_manual.py

Purpose:
  - Records a short clip from the default (or configured) microphone without VAD
  - Uses the repo's `WHISPER_MODEL` and device settings from `config.py`
  - Prints RMS/Peak and the Whisper transcription

This is a quick-and-dirty manual test (not a unit test). It avoids importing
the full `VoiceAssistant` class to keep startup light and focused on Whisper.
"""

from config import WHISPER_MODEL, get_device, get_fp16, MICROPHONE_INDEX
import speech_recognition as sr
import numpy as np
import time


def record_clip(duration_s=6):
    r = sr.Recognizer()
    mic_kwargs = {}
    if MICROPHONE_INDEX is not None:
        try:
            mic_kwargs['device_index'] = int(MICROPHONE_INDEX)
        except Exception:
            pass

    mic = sr.Microphone(**mic_kwargs)

    print("Adjusting for ambient noise (1s)...")
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
        print(f"Recording for {duration_s} seconds — speak now.")
        audio = r.listen(source, timeout=duration_s + 2, phrase_time_limit=duration_s)

    return audio


def transcribe_with_whisper(audio, model, language="en"):
    # Convert to 16 kHz int16 bytes as in main._transcribe_whisper
    wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
    audio_np = np.frombuffer(wav_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    if audio_np.size == 0:
        print("No audio captured (silent).")
        return None

    peak = float(np.abs(audio_np).max())
    rms = float(np.sqrt(np.mean(audio_np ** 2)))
    print(f"Audio RMS: {rms:.6f}, Peak: {peak:.6f}")

    # Try to use whisper helper to pad/trim if available
    try:
        from whisper import audio as whisper_audio
        audio_np = whisper_audio.pad_or_trim(audio_np)
    except Exception:
        pass

    # Save raw WAV for playback/inspection
    try:
        import soundfile as sf
        import os
        os.makedirs("logs", exist_ok=True)
        sf.write("logs/last_whisper_test_raw.wav", audio_np, 16000, subtype="PCM_16")
        print("Saved raw recording to logs/last_whisper_test_raw.wav")
    except Exception as e:
        print(f"Could not save raw WAV: {e}")

    # Attempt simple spectral gating noise reduction if available
    denoised = None
    try:
        import noisereduce as nr
        # Use a short initial segment as the noise profile (0.5s or less)
        srate = 16000
        noise_len = min(int(0.5 * srate), len(audio_np))
        if noise_len > 0:
            noise_clip = audio_np[:noise_len]
            denoised = nr.reduce_noise(y=audio_np, sr=srate, y_noise=noise_clip)
            try:
                sf.write("logs/last_whisper_test_denoised.wav", denoised, srate, subtype="PCM_16")
                print("Saved denoised recording to logs/last_whisper_test_denoised.wav")
            except Exception:
                pass
        else:
            denoised = audio_np
    except Exception as e:
        print(f"noisereduce not available or failed: {e}")
        denoised = audio_np

    # Normalize to avoid clipping issues when saving
    try:
        if denoised is not None and np.max(np.abs(denoised)) > 0:
            denoised = denoised / max(1e-8, np.max(np.abs(denoised)))
    except Exception:
        pass

    # Try transcribing the denoised file (prefer file path for Whisper)
    try:
        # If we saved the denoised file, prefer that path
        denoised_path = "logs/last_whisper_test_denoised.wav"
        import os
        if os.path.exists(denoised_path):
            result = model.transcribe(denoised_path, fp16=get_fp16(), language=language)
        else:
            # Fallback to transcribing numpy directly
            result = model.transcribe(denoised, fp16=get_fp16(), language=language)

        text = result.get("text", "").strip()
        return text
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        return None


def main():
    print(f"Loading Whisper model '{WHISPER_MODEL}' on device: {get_device()}")
    try:
        import whisper
        model = whisper.load_model(WHISPER_MODEL, device=get_device())
    except Exception as e:
        print("Failed to load Whisper model. Make sure 'whisper' is installed and a model is available.")
        print(e)
        return

    try:
        audio = record_clip(duration_s=6)
    except Exception as e:
        print(f"Failed to record audio from microphone: {e}")
        return

    text = transcribe_with_whisper(audio, model, language="en")
    print("\n--- Transcription Result ---")
    if text:
        print(text)
    else:
        print("(no transcription)")


if __name__ == "__main__":
    main()
