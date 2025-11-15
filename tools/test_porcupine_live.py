"""
Test Porcupine wake word detection with live audio level display
"""
import os
import struct
import numpy as np
from dotenv import load_dotenv

load_dotenv()

def create_level_bar(level, max_bars=30):
    """Create a visual level bar"""
    filled = int(level * max_bars)
    bar = "█" * filled + "░" * (max_bars - filled)
    return bar

def test_porcupine_with_levels():
    """Test Porcupine wake word detection with audio level visualization"""
    
    try:
        import pvporcupine
        from pvrecorder import PvRecorder
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install pvporcupine pvrecorder")
        return
    
    access_key = os.getenv("PORCUPINE_ACCESS_KEY")
    if not access_key:
        print("❌ PORCUPINE_ACCESS_KEY not found in .env")
        return
    
    # Get microphone index
    porcupine_mic = os.getenv("PORCUPINE_MICROPHONE_INDEX")
    if porcupine_mic and porcupine_mic != "":
        porcupine_mic = int(porcupine_mic)
    else:
        porcupine_mic = -1  # Default
    
    print("="*70)
    print("🎤 PORCUPINE WAKE WORD TEST WITH AUDIO LEVELS")
    print("="*70)
    
    # Find wake word file
    wake_word_file = None
    if os.path.exists("wake_words"):
        import glob
        ppn_files = glob.glob("wake_words/**/*.ppn", recursive=True)
        if ppn_files:
            wake_word_file = ppn_files[0]
            print(f"✓ Using wake word file: {os.path.basename(wake_word_file)}")
    
    try:
        # Initialize Porcupine
        if wake_word_file:
            porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[wake_word_file],
                sensitivities=[0.5]
            )
        else:
            print("Using built-in keyword: 'porcupine'")
            porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=["porcupine"],
                sensitivities=[0.5]
            )
        
        # Initialize recorder
        recorder = PvRecorder(
            device_index=porcupine_mic,
            frame_length=porcupine.frame_length
        )
        
        if porcupine_mic == -1:
            print("✓ Using default microphone")
        else:
            print(f"✓ Using microphone #{porcupine_mic}")
        
        print(f"\n🎯 Say the wake word to test detection")
        print("Press Ctrl+C to stop\n")
        
        recorder.start()
        
        while True:
            # Read audio frame
            pcm = recorder.read()
            
            # Calculate audio level
            audio_array = np.array(pcm, dtype=np.int16)
            level = np.abs(audio_array).mean() / 32768.0  # Normalize to 0-1
            
            # Create visual bar
            bar = create_level_bar(level)
            percentage = int(level * 100)
            
            # Check for wake word
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                print(f"\r🎉 WAKE WORD DETECTED! [{bar}] {percentage:3d}%")
                print("\n✓ Porcupine is working correctly!\n")
            else:
                print(f"\r🔊 [{bar}] {percentage:3d}%", end="", flush=True)
        
    except KeyboardInterrupt:
        print("\n\n✓ Test stopped")
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
    test_porcupine_with_levels()
