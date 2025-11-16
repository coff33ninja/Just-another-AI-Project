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

from config import WHISPER_MODEL, get_device, get_fp16
import speech_recognition as sr
import numpy as np
import time


def record_clip(duration_s=6):
    r = sr.Recognizer()

    # Use the default system microphone explicitly to avoid selecting a
    # device index that may enable driver-side noise cancellation.
    mic = sr.Microphone()

    print(f"Using default system microphone. Recording for {duration_s} seconds — speak now.")
    with mic as source:
        # Do NOT call adjust_for_ambient_noise here to avoid any automatic
        # preprocessing that can interact poorly with hardware drivers.
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

    # Save raw WAV for playback/inspection and transcribe from the file to
    # avoid any in-memory normalization that might mask driver behavior.
    try:
        import soundfile as sf
        import os
        os.makedirs("logs", exist_ok=True)
        sf.write("logs/last_whisper_test_raw.wav", audio_np, 16000, subtype="PCM_16")
        print("Saved raw recording to logs/last_whisper_test_raw.wav")
    except Exception as e:
        print(f"Could not save raw WAV: {e}")

    # Transcribe using the saved raw WAV file (no denoising applied).
    try:
        raw_path = "logs/last_whisper_test_raw.wav"
        result = model.transcribe(raw_path, fp16=get_fp16(), language=language)
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
