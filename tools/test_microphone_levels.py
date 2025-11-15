"""
Real-time microphone level meter to test if audio is being captured
"""
import numpy as np
import sounddevice as sd
import os
from dotenv import load_dotenv

load_dotenv()

def create_level_bar(level, max_bars=50):
    """Create a visual level bar"""
    filled = int(level * max_bars)
    bar = "█" * filled + "░" * (max_bars - filled)
    return bar

def test_microphone_levels():
    """Display real-time audio levels from microphone"""
    
    # Get microphone index from config
    mic_index = os.getenv("MICROPHONE_INDEX")
    if mic_index:
        mic_index = int(mic_index)
    
    print("="*70)
    print("🎤 MICROPHONE LEVEL METER")
    print("="*70)
    
    if mic_index is not None:
        print(f"Testing microphone #{mic_index}")
    else:
        print("Testing default microphone")
    
    print("\nSpeak into your microphone to see the levels...")
    print("Press Ctrl+C to stop\n")
    
    def audio_callback(indata, frames, time, status):
        """Process audio and display level"""
        if status:
            print(f"Status: {status}")
        
        # Calculate RMS (Root Mean Square) level
        volume_norm = np.linalg.norm(indata) * 10
        level = min(volume_norm / 100, 1.0)  # Normalize to 0-1
        
        # Create visual bar
        bar = create_level_bar(level)
        
        # Display with percentage
        percentage = int(level * 100)
        print(f"\r🔊 Level: [{bar}] {percentage:3d}%", end="", flush=True)
    
    try:
        # Open audio stream
        with sd.InputStream(
            device=mic_index,
            channels=1,
            samplerate=16000,
            blocksize=1024,
            callback=audio_callback
        ):
            print("Listening...")
            # Keep running until interrupted
            sd.sleep(1000000)
    
    except KeyboardInterrupt:
        print("\n\n✓ Test stopped")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Check if microphone is connected")
        print("  - Try a different MICROPHONE_INDEX in .env")
        print("  - Run 'python tools/audio_setup.py' to list devices")

if __name__ == "__main__":
    test_microphone_levels()
