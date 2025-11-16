#!/usr/bin/env python3
"""
Quick test for Porcupine wake word detection with visual feedback
Run this before running main.py to verify wake words are being detected
"""

import os
from dotenv import load_dotenv

def test_wake_word():
    """Test wake word detection with live audio visualization"""
    load_dotenv()
    
    try:
        import pvporcupine
        from pvrecorder import PvRecorder
        import numpy as np
        import time
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install pvporcupine pvrecorder")
        return
    
    access_key = os.getenv("PORCUPINE_ACCESS_KEY")
    if not access_key:
        print("❌ PORCUPINE_ACCESS_KEY not set in .env")
        return
    
    print("="*70)
    print("🎤 PORCUPINE WAKE WORD TEST")
    print("="*70)
    
    # Find wake word file
    from pathlib import Path
    wake_words_dir = Path("wake_words")
    ppn_files = list(wake_words_dir.glob("**/*.ppn"))
    
    if not ppn_files:
        print("❌ No .ppn wake word files found in wake_words/")
        return
    
    wake_word_file = ppn_files[0]
    print(f"Testing wake word: {wake_word_file.parent.name}")
    print(f"File: {wake_word_file.name}\n")
    
    try:
        # Initialize Porcupine
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[str(wake_word_file)],
            sensitivities=[float(os.getenv("PORCUPINE_SENSITIVITY", "0.5"))]
        )
        
        # Initialize recorder
        mic_index = os.getenv("PORCUPINE_MICROPHONE_INDEX")
        if mic_index and mic_index != "":
            mic_index = int(mic_index)
        else:
            mic_index = -1  # Default
        
        recorder = PvRecorder(
            device_index=mic_index,
            frame_length=porcupine.frame_length
        )
        
        print("🎯 Instructions:")
        print("  1. Say the wake word clearly")
        print("  2. Watch for 'DETECTED!' message")
        print("  3. Press Ctrl+C to stop\n")
        
        print(f"🎙️  Listening with sensitivity: {os.getenv('PORCUPINE_SENSITIVITY', '0.5')}")
        print("  Say 'hey spark' now...\n")
        
        recorder.start()
        detection_count = 0
        frame_count = 0
        
        while True:
            # Read audio frame
            pcm = recorder.read()
            frame_count += 1
            
            # Process with Porcupine
            keyword_index = porcupine.process(pcm)
            
            # Show progress indicator
            indicators = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            print(f"\r{indicators[frame_count % len(indicators)]} Listening... ({frame_count} frames)", end="", flush=True)
            
            # Check for detection
            if keyword_index >= 0:
                detection_count += 1
                print(f"\n\n🎉 WAKE WORD DETECTED! (Detection #{detection_count})")
                print(f"   Frame: {frame_count}, Keyword Index: {keyword_index}")
                print("\n  Say it again or press Ctrl+C to exit...\n")
    
    except KeyboardInterrupt:
        print("\n\n✓ Test stopped")
        if detection_count > 0:
            print(f"✓ Detected wake word {detection_count} time(s)")
            print("✓ Porcupine is working! Run 'python main.py' to start the assistant.")
        else:
            print("⚠️  No detections. Tips:")
            print("  - Speak clearly and at normal volume")
            print("  - Check microphone is working with audio_setup.py")
            print("  - Try increasing PORCUPINE_SENSITIVITY in .env (0.5 → 0.7)")
    
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'recorder' in locals():
            recorder.stop()
            recorder.delete()
        if 'porcupine' in locals():
            porcupine.delete()

if __name__ == "__main__":
    test_wake_word()
