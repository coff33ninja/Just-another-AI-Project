"""
Complete Audio Setup Tool
Test and configure both microphone and speakers
"""

import speech_recognition as sr
import sounddevice as sd
import numpy as np
import time


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def list_all_devices():
    """List all audio devices"""
    print_header("AUDIO DEVICES")
    
    devices = sd.query_devices()
    
    print("\n📥 INPUT DEVICES (Microphones):")
    input_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  [{i:2d}] {device['name']}")
            input_devices.append(i)
    
    print("\n📤 OUTPUT DEVICES (Speakers):")
    output_devices = []
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            print(f"  [{i:2d}] {device['name']}")
            output_devices.append(i)
    
    return input_devices, output_devices


def test_speaker(device_index=None):
    """Test a speaker by playing a tone"""
    print_header("SPEAKER TEST")
    
    try:
        if device_index is not None:
            device_info = sd.query_devices(device_index)
            print(f"\n🔊 Testing: {device_info['name']}")
        else:
            print("\n🔊 Testing default speaker")
        
        print("   Playing test tone (440 Hz A note)...")
        
        # Generate pleasant test tone
        duration = 1.5
        sample_rate = 44100
        frequency = 440.0
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        tone = np.sin(2 * np.pi * frequency * t)
        
        # Add fade in/out
        fade_samples = int(sample_rate * 0.05)
        tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
        tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        tone *= 0.3  # 30% volume
        
        if device_index is not None:
            sd.play(tone, sample_rate, device=device_index)
        else:
            sd.play(tone, sample_rate)
        sd.wait()
        
        print("   ✓ Tone played")
        response = input("\n   Did you hear the tone? (y/n): ").strip().lower()
        return response == 'y'
    
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_microphone(device_index=None):
    """Test a microphone"""
    print_header("MICROPHONE TEST")
    
    try:
        if device_index is not None:
            mics = sr.Microphone.list_microphone_names()
            print(f"\n🎤 Testing: {mics[device_index]}")
        else:
            print("\n🎤 Testing default microphone")
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = False
        
        if device_index is not None:
            mic = sr.Microphone(device_index=device_index)
        else:
            mic = sr.Microphone()
        
        with mic as source:
            print("   Adjusting for ambient noise (2 seconds)...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"   Energy threshold: {recognizer.energy_threshold:.1f}")
            
            # Display test phrase
            test_phrase = "Hello, this is a microphone test"
            print(f"\n   📝 Please say: '{test_phrase}'")
            print("   🎙️  Get ready... (starting in 3 seconds)")
            time.sleep(3)
            
            print("   🔴 RECORDING NOW - Speak clearly!")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
        
        print("   ✓ Audio captured")
        print(f"   Audio size: {len(audio.get_wav_data())} bytes")
        
        # Analyze audio level
        audio_data = np.frombuffer(audio.get_wav_data(), dtype=np.int16)
        rms = np.sqrt(np.mean(audio_data**2))
        max_amplitude = np.max(np.abs(audio_data))
        print(f"   Signal strength: RMS={int(rms)}, Peak={int(max_amplitude)}")
        
        if rms < 50:
            print("   ⚠ WARNING: Very weak signal! Microphone may be too quiet or muted.")
        
        # Try Whisper transcription first (more accurate)
        try:
            import whisper
            print("\n   🔄 Transcribing with Whisper (this may take a moment)...")
            model = whisper.load_model("base")
            
            audio_np = audio_data.astype(np.float32) / 32768.0
            
            # Use language hint and adjust settings for better detection
            result = model.transcribe(
                audio_np,
                language="en",
                fp16=False,
                initial_prompt="Hello, this is a microphone test"
            )
            
            transcribed_text = result["text"].strip()
            
            if transcribed_text:
                print(f"   ✓ Heard: '{transcribed_text}'")
                
                # Check if it's close to the test phrase
                heard_lower = transcribed_text.lower()
                if "hello" in heard_lower or "microphone" in heard_lower or "test" in heard_lower:
                    print("   ✓ Microphone is working well!")
                else:
                    print("   ⚠ Audio captured but phrase doesn't match expected")
                    print("   💡 Still, the microphone is capturing speech!")
                
                return True
            else:
                print("   ⚠ No speech detected in audio")
                print("   💡 Audio was captured but Whisper couldn't transcribe it")
                
                # If we have decent signal, still consider it working
                if rms > 100:
                    print("   ℹ️  Signal strength is good - microphone may still work")
                    
                    # Offer to play back the audio
                    playback = input("   Play back what was recorded? (y/n): ").strip().lower()
                    if playback == 'y':
                        print("   🔊 Playing back recorded audio...")
                        sd.play(audio_np, 16000)
                        sd.wait()
                    
                    accept = input("   Mark this microphone as working? (y/n): ").strip().lower()
                    return accept == 'y'
                
                return False
        
        except ImportError:
            print("   ⚠ Whisper not available, using Google STT...")
            try:
                text = recognizer.recognize_google(audio)
                print(f"   ✓ Heard: '{text}'")
                return True
            except Exception as e:
                print(f"   ✗ Recognition failed: {e}")
                return False
    
    except sr.WaitTimeoutError:
        print("   ✗ Timeout - no speech detected within 10 seconds")
        print("   💡 Tips:")
        print("      - Speak louder and clearer")
        print("      - Move closer to the microphone")
        print("      - Check if microphone is muted in Windows settings")
        print("      - Try a different microphone")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_audio_loopback(speaker_index=None, mic_index=None):
    """Test full audio loop: speaker → microphone"""
    print_header("AUDIO LOOPBACK TEST")
    
    print("\n🔄 This test plays a tone through speakers and listens with microphone")
    print("   Make sure speakers are not muted and microphone is enabled")
    
    try:
        # Generate test tone
        duration = 2.0
        sample_rate = 44100
        frequency = 1000.0  # 1kHz
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        tone = np.sin(2 * np.pi * frequency * t) * 0.3
        
        print("\n   🔊 Playing test tone...")
        if speaker_index is not None:
            sd.play(tone, sample_rate, device=speaker_index, blocking=False)
        else:
            sd.play(tone, sample_rate, blocking=False)
        
        time.sleep(0.5)
        
        print("   🎤 Listening with microphone...")
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_threshold = False
        
        if mic_index is not None:
            mic = sr.Microphone(device_index=mic_index)
        else:
            mic = sr.Microphone()
        
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=1.5)
                audio_data = np.frombuffer(audio.get_wav_data(), dtype=np.int16)
                
                rms = np.sqrt(np.mean(audio_data**2))
                
                sd.wait()
                
                print(f"   Signal strength: {int(rms)}")
                
                if rms > 100:
                    print("   ✓ Loopback successful! Both devices working.")
                    return True
                else:
                    print("   ⚠ Weak signal. Speakers may be too quiet.")
                    return False
        
        except sr.WaitTimeoutError:
            sd.wait()
            print("   ✗ Microphone didn't detect the tone")
            return False
    
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def save_config(mic_index, speaker_index):
    """Save configuration to .env file"""
    print_header("SAVE CONFIGURATION")
    
    print("\n📝 Configuration:")
    print(f"   Microphone: {mic_index}")
    print(f"   Speaker: {speaker_index}")
    
    save = input("\n   Save to .env file? (y/n): ").strip().lower()
    
    if save == 'y':
        try:
            # Read existing .env
            env_lines = []
            try:
                with open('.env', 'r') as f:
                    env_lines = f.readlines()
            except FileNotFoundError:
                pass
            
            # Remove old audio config
            env_lines = [line for line in env_lines 
                        if not line.startswith('MICROPHONE_INDEX=') 
                        and not line.startswith('SPEAKER_INDEX=')]
            
            # Add new config
            if not env_lines or not env_lines[-1].endswith('\n'):
                env_lines.append('\n')
            
            env_lines.append('\n# Audio Device Configuration\n')
            env_lines.append(f'MICROPHONE_INDEX={mic_index}\n')
            env_lines.append(f'SPEAKER_INDEX={speaker_index}\n')
            
            # Write back
            with open('.env', 'w') as f:
                f.writelines(env_lines)
            
            print("   ✓ Configuration saved to .env")
            return True
        
        except Exception as e:
            print(f"   ✗ Error saving: {e}")
            return False
    
    return False


def interactive_setup():
    """Interactive audio setup wizard"""
    print("\n" + "=" * 70)
    print("  🎵 VOICE ASSISTANT - AUDIO SETUP WIZARD")
    print("=" * 70)
    print("\n  This wizard will help you configure your audio devices.")
    print("  Press Ctrl+C at any time to exit.\n")
    
    try:
        # List devices
        input_devices, output_devices = list_all_devices()
        
        # Test speakers
        print("\n" + "-" * 70)
        print("STEP 1: Configure Speakers")
        print("-" * 70)
        
        speaker_index = None
        while True:
            choice = input("\nEnter speaker number to test (or 'skip'): ").strip()
            
            if choice.lower() == 'skip':
                break
            
            try:
                idx = int(choice)
                if idx in output_devices:
                    if test_speaker(idx):
                        speaker_index = idx
                        print(f"\n✓ Speaker #{idx} selected")
                        break
                    else:
                        retry = input("   Try another speaker? (y/n): ").strip().lower()
                        if retry != 'y':
                            break
                else:
                    print(f"   Invalid speaker index. Choose from: {output_devices}")
            except ValueError:
                print("   Please enter a number")
        
        # Test microphones
        print("\n" + "-" * 70)
        print("STEP 2: Configure Microphone")
        print("-" * 70)
        
        mic_index = None
        while True:
            choice = input("\nEnter microphone number to test (or 'skip'): ").strip()
            
            if choice.lower() == 'skip':
                break
            
            try:
                idx = int(choice)
                if idx in input_devices:
                    if test_microphone(idx):
                        mic_index = idx
                        print(f"\n✓ Microphone #{idx} selected")
                        break
                    else:
                        retry = input("   Try another microphone? (y/n): ").strip().lower()
                        if retry != 'y':
                            break
                else:
                    print(f"   Invalid microphone index. Choose from: {input_devices}")
            except ValueError:
                print("   Please enter a number")
        
        # Loopback test
        if speaker_index is not None and mic_index is not None:
            print("\n" + "-" * 70)
            print("STEP 3: Full Audio Test")
            print("-" * 70)
            
            test = input("\nRun loopback test? (y/n): ").strip().lower()
            if test == 'y':
                test_audio_loopback(speaker_index, mic_index)
        
        # Save configuration
        if mic_index is not None or speaker_index is not None:
            save_config(
                mic_index if mic_index is not None else 'None',
                speaker_index if speaker_index is not None else 'None'
            )
        
        print("\n" + "=" * 70)
        print("  ✓ Audio setup complete!")
        print("=" * 70)
        print("\n  You can now run: python main.py\n")
    
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled by user\n")


if __name__ == "__main__":
    interactive_setup()
