"""Select and test specific microphone"""
import speech_recognition as sr
import numpy as np

def test_specific_mic(mic_index):
    """Test a specific microphone"""
    print(f"\n🎤 Testing Microphone #{mic_index}")
    print("=" * 60)
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # Start with default
    recognizer.dynamic_energy_threshold = False  # Don't auto-adjust
    
    try:
        with sr.Microphone(device_index=mic_index) as source:
            print(f"✓ Microphone initialized")
            
            print("\n🎙️  Say something NOW (you have 10 seconds)...")
            print("   Speak clearly and at normal volume")
            
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            
            print("✓ Audio captured!")
            print(f"  Audio length: {len(audio.get_wav_data())} bytes")
            
            # Try Whisper
            try:
                import whisper
                print("\n🔄 Transcribing with Whisper...")
                model = whisper.load_model("base")
                
                audio_np = np.frombuffer(audio.get_wav_data(), dtype=np.int16).astype(np.float32) / 32768.0
                result = model.transcribe(audio_np)
                
                print(f"✓ Whisper heard: '{result['text']}'")
                return True
                
            except Exception as e:
                print(f"❌ Whisper error: {e}")
                return False
            
    except sr.WaitTimeoutError:
        print("❌ Timeout - no speech detected")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎤 Microphone Selector\n")
    
    # List microphones
    mics = sr.Microphone.list_microphone_names()
    
    print("📋 Available Input Microphones:")
    input_mics = []
    for index, name in enumerate(mics):
        # Filter for likely input devices
        if any(keyword in name.lower() for keyword in ['microphone', 'mic', 'input', 'capture']):
            print(f"  [{index}] {name}")
            input_mics.append(index)
    
    print("\n" + "=" * 60)
    print("Enter microphone number to test (or 'q' to quit)")
    print("Recommended: Try 'Realtek High Definition Audio' first")
    print("=" * 60)
    
    while True:
        choice = input("\nMicrophone #: ").strip()
        
        if choice.lower() == 'q':
            break
        
        try:
            mic_index = int(choice)
            if mic_index < 0 or mic_index >= len(mics):
                print(f"❌ Invalid index. Choose 0-{len(mics)-1}")
                continue
            
            success = test_specific_mic(mic_index)
            
            if success:
                print(f"\n✅ Microphone #{mic_index} works!")
                print(f"\nTo use this microphone, add to your .env file:")
                print(f"MICROPHONE_INDEX={mic_index}")
                
                save = input("\nSave this to .env? (y/n): ").strip().lower()
                if save == 'y':
                    with open('.env', 'a') as f:
                        f.write(f"\n# Microphone Configuration\nMICROPHONE_INDEX={mic_index}\n")
                    print("✓ Saved to .env")
                break
        
        except ValueError:
            print("❌ Please enter a number")
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled")
            break

if __name__ == "__main__":
    main()
