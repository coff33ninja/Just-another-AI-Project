"""
Find which PvRecorder device actually works with your microphone
"""
import os
import time
import numpy as np
from dotenv import load_dotenv

load_dotenv()

def test_all_pvrecorder_devices():
    """Test all PvRecorder devices to find which one captures audio"""
    try:
        from pvrecorder import PvRecorder
    except ImportError:
        print("❌ PvRecorder not installed")
        print("Install with: pip install pvrecorder")
        return
    
    print("="*70)
    print("🔍 TESTING ALL PVRECORDER DEVICES")
    print("="*70)
    
    # Get available devices
    devices = PvRecorder.get_available_devices()
    print(f"\nFound {len(devices)} devices:")
    for i, device in enumerate(devices):
        print(f"  [{i}] {device}")
    
    print("\n" + "="*70)
    print("Testing each device for 3 seconds...")
    print("SPEAK INTO YOUR MICROPHONE during each test!")
    print("="*70 + "\n")
    
    working_devices = []
    
    for i in range(len(devices)):
        print(f"\n[Device {i}] {devices[i]}")
        print("-" * 50)
        
        try:
            recorder = PvRecorder(device_index=i, frame_length=512)
            recorder.start()
            
            print("🎤 Recording for 3 seconds - SPEAK NOW!")
            
            max_level = 0
            total_level = 0
            frames = 0
            
            # Record for 3 seconds
            for _ in range(int(3 * 16000 / 512)):  # 3 seconds at 16kHz
                pcm = recorder.read()
                audio_array = np.array(pcm, dtype=np.int16)
                level = np.abs(audio_array).mean() / 32768.0
                
                max_level = max(max_level, level)
                total_level += level
                frames += 1
                
                # Show live meter
                bar_length = int(level * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)
                print(f"\r  [{bar}] {int(level * 100):3d}%", end="", flush=True)
            
            recorder.stop()
            recorder.delete()
            
            avg_level = total_level / frames if frames > 0 else 0
            
            print(f"\n  Max level: {int(max_level * 100)}%")
            print(f"  Avg level: {int(avg_level * 100)}%")
            
            if max_level > 0.05:  # If we detected significant audio
                print(f"  ✓ WORKING - This device captures audio!")
                working_devices.append(i)
            else:
                print(f"  ✗ No audio detected")
        
        except Exception as e:
            print(f"\n  ✗ Error: {e}")
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    if working_devices:
        print(f"\n✓ Found {len(working_devices)} working device(s):")
        for i in working_devices:
            print(f"  Device {i}: {devices[i]}")
        
        recommended = working_devices[0]
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Set PORCUPINE_MICROPHONE_INDEX={recommended} in your .env file")
        
        # Ask if user wants to update .env
        response = input(f"\nUpdate .env with device {recommended}? (y/n): ").lower()
        if response == 'y':
            update_env_file(recommended)
    else:
        print("\n❌ No working devices found!")
        print("\nTroubleshooting:")
        print("  1. Make sure your microphone is connected and not muted")
        print("  2. Check Windows privacy settings (Microphone access)")
        print("  3. Close other apps that might be using the microphone")
        print("  4. Try running as administrator")
        print("  5. Use builtin wake word detection instead:")
        print("     Set WAKE_WORD_ENGINE=builtin in .env")

def update_env_file(device_index):
    """Update .env file with the working device index"""
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('PORCUPINE_MICROPHONE_INDEX='):
                lines[i] = f'PORCUPINE_MICROPHONE_INDEX={device_index}\n'
                updated = True
                break
        
        if updated:
            with open('.env', 'w') as f:
                f.writelines(lines)
            print(f"✓ Updated .env: PORCUPINE_MICROPHONE_INDEX={device_index}")
        else:
            print("⚠ Could not find PORCUPINE_MICROPHONE_INDEX in .env")
    
    except Exception as e:
        print(f"❌ Error updating .env: {e}")

if __name__ == "__main__":
    test_all_pvrecorder_devices()
