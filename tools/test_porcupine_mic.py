"""
Test Porcupine PvRecorder with different microphone indices
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_pvrecorder():
    """Test PvRecorder with different device indices"""
    try:
        from pvrecorder import PvRecorder
        
        print("Testing PvRecorder microphone compatibility...\n")
        
        # Get available devices
        devices = PvRecorder.get_available_devices()
        print(f"Available audio devices ({len(devices)}):")
        for i, device in enumerate(devices):
            print(f"  [{i}] {device}")
        
        print("\n" + "="*60)
        
        # Get configured microphone index
        mic_index = os.getenv("MICROPHONE_INDEX")
        if mic_index:
            mic_index = int(mic_index)
            print(f"\nTesting configured microphone #{mic_index}...")
            
            try:
                recorder = PvRecorder(device_index=mic_index, frame_length=512)
                print(f"✓ SUCCESS: Microphone #{mic_index} works with PvRecorder")
                recorder.delete()
            except Exception as e:
                print(f"✗ FAILED: Microphone #{mic_index} - {e}")
                print("\nTrying default microphone (-1)...")
                try:
                    recorder = PvRecorder(device_index=-1, frame_length=512)
                    print("✓ SUCCESS: Default microphone works")
                    recorder.delete()
                    print("\n💡 Suggestion: Remove MICROPHONE_INDEX from .env to use default")
                except Exception as e2:
                    print(f"✗ FAILED: Default microphone - {e2}")
        else:
            print("\nNo MICROPHONE_INDEX configured, testing default...")
            try:
                recorder = PvRecorder(device_index=-1, frame_length=512)
                print("✓ SUCCESS: Default microphone works")
                recorder.delete()
            except Exception as e:
                print(f"✗ FAILED: Default microphone - {e}")
        
        print("\n" + "="*60)
        print("\n💡 Tips:")
        print("  - PvRecorder may use different device indices than speech_recognition")
        print("  - Try removing MICROPHONE_INDEX from .env to use default")
        print("  - Make sure your microphone is not in use by another application")
        print("  - Some USB microphones may not be compatible with PvRecorder")
        
    except ImportError:
        print("❌ PvRecorder not installed")
        print("Install with: pip install pvrecorder")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pvrecorder()
