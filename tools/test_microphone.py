"""Test microphone and speech recognition"""
import speech_recognition as sr
import numpy as np

def test_microphone():
    """Test if microphone is working"""
    print("🎤 Testing Microphone Setup\n")
    print("=" * 60)
    
    # List available microphones
    print("\n📋 Available Microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  [{index}] {name}")
    
    # Test default microphone
    print("\n🔧 Testing Default Microphone...")
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print(f"✓ Microphone initialized")
            print(f"  Default energy threshold: {recognizer.energy_threshold}")
            
            print("\n🔊 Adjusting for ambient noise (2 seconds)...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"  Adjusted energy threshold: {recognizer.energy_threshold}")
            
            print("\n🎙️  Say something (you have 5 seconds)...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            print("✓ Audio captured!")
            print(f"  Audio length: {len(audio.get_wav_data())} bytes")
            
            # Try Whisper if available
            try:
                import whisper
                print("\n🔄 Testing Whisper transcription...")
                model = whisper.load_model("base")
                
                audio_np = np.frombuffer(audio.get_wav_data(), dtype=np.int16).astype(np.float32) / 32768.0
                result = model.transcribe(audio_np)
                
                print(f"✓ Whisper heard: '{result['text']}'")
                
            except ImportError:
                print("⚠️  Whisper not available")
            except Exception as e:
                print(f"❌ Whisper error: {e}")
            
            # Try Google STT
            try:
                print("\n🔄 Testing Google STT...")
                text = recognizer.recognize_google(audio)
                print(f"✓ Google heard: '{text}'")
            except sr.UnknownValueError:
                print("❌ Google couldn't understand audio")
            except sr.RequestError as e:
                print(f"❌ Google STT error: {e}")
            
    except sr.WaitTimeoutError:
        print("❌ Timeout - no speech detected")
        print("   Try speaking louder or closer to the microphone")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("\n💡 Tips:")
    print("  - Make sure your microphone is not muted")
    print("  - Check Windows sound settings")
    print("  - Try speaking louder and closer to the mic")
    print("  - Reduce background noise")

if __name__ == "__main__":
    test_microphone()
