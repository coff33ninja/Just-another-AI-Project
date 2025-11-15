"""
Audio Plugin - Test and configure audio devices (microphone and speakers)
"""

from plugins import Plugin
from typing import Dict, Any
import speech_recognition as sr
import numpy as np
import sounddevice as sd
import time


class AudioPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.description = "Test and configure audio devices (microphone and speakers)"
        self.triggers = [
            "microphone", "mic test", "test microphone", "list microphones",
            "speaker", "speakers", "test speakers", "list speakers", "test audio",
            "audio test", "sound test", "list audio"
        ]
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> str:
        """Handle audio configuration requests"""
        user_lower = user_input.lower()
        
        # Microphone commands
        if "list" in user_lower and ("mic" in user_lower or "microphone" in user_lower):
            return self._list_microphones()
        elif "test" in user_lower and ("mic" in user_lower or "microphone" in user_lower):
            return self._test_current_microphone()
        
        # Speaker commands
        elif "list" in user_lower and ("speaker" in user_lower or "output" in user_lower):
            return self._list_speakers()
        elif "test" in user_lower and ("speaker" in user_lower or "output" in user_lower):
            return self._test_speakers()
        
        # General audio commands
        elif "list" in user_lower and "audio" in user_lower:
            return self._list_all_devices()
        elif "test" in user_lower and "audio" in user_lower:
            return self._test_audio_loop()
        
        else:
            return (
                "I can help with audio setup:\n"
                "- 'list microphones' - Show input devices\n"
                "- 'test microphone' - Test current microphone\n"
                "- 'list speakers' - Show output devices\n"
                "- 'test speakers' - Play test sound\n"
                "- 'test audio' - Full loopback test (speaker → mic)"
            )
    
    def _list_microphones(self) -> str:
        """List available microphones"""
        try:
            mics = sr.Microphone.list_microphone_names()
            
            # Filter for input devices
            input_mics = []
            for index, name in enumerate(mics):
                if any(keyword in name.lower() for keyword in ['microphone', 'mic', 'input', 'capture']):
                    input_mics.append(f"[{index}] {name}")
            
            if input_mics:
                response = "Available microphones:\n" + "\n".join(input_mics[:10])
                response += "\n\nTo select: Add MICROPHONE_INDEX=<number> to .env"
                return response
            else:
                return "No input microphones found."
        
        except Exception as e:
            return f"Error listing microphones: {e}"
    
    def _list_speakers(self) -> str:
        """List available speakers/output devices"""
        try:
            devices = sd.query_devices()
            
            output_devices = []
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    name = device['name']
                    output_devices.append(f"[{i}] {name}")
            
            if output_devices:
                response = "Available speakers:\n" + "\n".join(output_devices[:10])
                response += "\n\nTo select: Add SPEAKER_INDEX=<number> to .env"
                return response
            else:
                return "No output devices found."
        
        except Exception as e:
            return f"Error listing speakers: {e}"
    
    def _list_all_devices(self) -> str:
        """List all audio devices"""
        try:
            devices = sd.query_devices()
            
            inputs = []
            outputs = []
            
            for i, device in enumerate(devices):
                name = device['name']
                if device['max_input_channels'] > 0:
                    inputs.append(f"[{i}] {name}")
                if device['max_output_channels'] > 0:
                    outputs.append(f"[{i}] {name}")
            
            response = "INPUT DEVICES:\n" + "\n".join(inputs[:8])
            response += "\n\nOUTPUT DEVICES:\n" + "\n".join(outputs[:8])
            response += "\n\nAdd to .env: MICROPHONE_INDEX=<in> SPEAKER_INDEX=<out>"
            return response
        
        except Exception as e:
            return f"Error listing devices: {e}"
    
    def _test_current_microphone(self) -> str:
        """Test the current microphone"""
        try:
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = False
            
            with sr.Microphone() as source:
                print("\n🎤 Testing microphone - say something...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                
                # Try to transcribe
                try:
                    import whisper
                    model = whisper.load_model("base")
                    audio_np = np.frombuffer(audio.get_wav_data(), dtype=np.int16).astype(np.float32) / 32768.0
                    result = model.transcribe(audio_np)
                    
                    if result["text"].strip():
                        return f"✓ Microphone works! I heard: {result['text']}"
                    else:
                        return "⚠ Microphone captured audio but no speech detected."
                
                except Exception:
                    # Fallback to Google
                    text = recognizer.recognize_google(audio)
                    return f"✓ Microphone works! I heard: {text}"
        
        except sr.WaitTimeoutError:
            return "✗ Microphone test failed: No speech detected. Try speaking louder."
        except Exception as e:
            return f"✗ Microphone test failed: {e}"
    
    def _test_speakers(self) -> str:
        """Test speakers by playing a tone"""
        try:
            print("\n🔊 Testing speakers - playing test tone...")
            
            # Generate a pleasant test tone (440 Hz A note)
            duration = 1.0  # seconds
            sample_rate = 44100
            frequency = 440.0
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            # Create a tone with fade in/out to avoid clicks
            tone = np.sin(2 * np.pi * frequency * t)
            fade_samples = int(sample_rate * 0.05)  # 50ms fade
            tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
            tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            tone *= 0.3  # Reduce volume to 30%
            
            sd.play(tone, sample_rate)
            sd.wait()
            
            return "✓ Test tone played. Did you hear a beep? If not, check speaker connections and system volume."
        
        except Exception as e:
            return f"✗ Speaker test failed: {e}"
    
    def _test_audio_loop(self) -> str:
        """Test full audio loop: play tone and try to capture it"""
        try:
            print("\n🔊 Testing audio loopback...")
            print("   Playing test tone through speakers...")
            
            # Generate test tone
            duration = 2.0
            sample_rate = 44100
            frequency = 1000.0  # 1kHz test tone
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            tone = np.sin(2 * np.pi * frequency * t) * 0.3
            
            # Play tone in background
            sd.play(tone, sample_rate, blocking=False)
            
            # Wait a moment then try to capture
            time.sleep(0.5)
            
            print("   Listening with microphone...")
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 200
            recognizer.dynamic_energy_threshold = False
            
            try:
                with sr.Microphone() as source:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=1.5)
                    audio_data = np.frombuffer(audio.get_wav_data(), dtype=np.int16)
                    
                    # Check if we captured significant audio
                    rms = np.sqrt(np.mean(audio_data**2))
                    
                    sd.wait()  # Wait for playback to finish
                    
                    if rms > 100:
                        return f"✓ Audio loopback successful! Speakers and microphone are working. (Signal strength: {int(rms)})"
                    else:
                        return f"⚠ Weak signal detected ({int(rms)}). Speakers may be too quiet or microphone too far."
            
            except sr.WaitTimeoutError:
                sd.wait()
                return "⚠ Microphone didn't detect the test tone. Check if speakers are playing and microphone is working."
        
        except Exception as e:
            return f"✗ Audio loopback test failed: {e}"
