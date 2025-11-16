import speech_recognition as sr
import google.generativeai as genai
import sounddevice as sd
import numpy as np
import random
import threading
import time
import os
from config import (
    GEMINI_API_KEY, GEMINI_MODEL, load_personality,
    WAKE_WORD_ENGINE, PORCUPINE_ACCESS_KEY, PORCUPINE_SENSITIVITY,
    SPEECH_RECOGNITION_ENGINE, WHISPER_MODEL,
    VAD_ENABLED, VAD_SENSITIVITY,
    ENABLE_STREAMING, PLUGINS_ENABLED, PLUGINS_DIR,
    MICROPHONE_INDEX, PORCUPINE_MICROPHONE_INDEX, SPEAKER_INDEX,
    get_device, get_fp16
)
import config as cfg
import sys
from plugins import PluginManager

class VoiceAssistant:
    def __init__(self, personality_path=None):
        # Load personality
        self.personality = load_personality(personality_path)
        self.wake_word = self.personality["wake_word"].lower()
        self.is_awake = False
        
        # Setup device (CPU/GPU)
        self.device = get_device()
        print(f"🖥️  Using device: {self.device.upper()}")
        # Decide whether to use fp16 based on config.auto or override
        try:
            self.use_fp16 = get_fp16()
        except Exception:
            self.use_fp16 = False
        print(f"  Using fp16: {self.use_fp16}")
        
        # Initialize wake word detection
        self.wake_engine = None
        self.wake_type = None
        self._initialize_wake_word()
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        # Start with a reasonable fixed threshold but allow dynamic adjustment
        # so short commands after the wake word are captured reliably.
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize microphone with specific device if configured
        if MICROPHONE_INDEX is not None:
            self.microphone = sr.Microphone(device_index=MICROPHONE_INDEX)
            print(f"🎤 Using microphone #{MICROPHONE_INDEX}")
        else:
            self.microphone = sr.Microphone()
            print("🎤 Using default microphone")
        
        # Initialize speech recognition engine
        self.stt_engine = None
        self.stt_type = None
        self._initialize_speech_recognition()
        
        # Initialize VAD if enabled
        self.vad_model = None
        if VAD_ENABLED:
            self._initialize_vad()

        # Start interactive tuner if running in a TTY (allow runtime tuning)
        try:
            if sys.stdin and sys.stdin.isatty():
                self._start_interactive_tuner()
        except Exception:
            pass
        
        # Initialize Gemini with personality
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=self.personality["system_prompt"]
        )
        self.chat = self.model.start_chat(history=[])
        
        # Initialize TTS with fallback
        self.tts_engine = None
        self.tts_type = None
        self.sample_rate = 24000
        print("🔊 Loading TTS models...")
        self._initialize_tts()
        
        # Initialize plugin system
        self.plugin_manager = None
        if PLUGINS_ENABLED:
            print("🔌 Loading plugins...")
            self.plugin_manager = PluginManager(PLUGINS_DIR)
        
        print(f"\n✨ {self.personality['name']} initialized!")
        print(f"🎤 Wake word: '{self.wake_word}' (Engine: {self.wake_type})")
        print(f"🎙️  Speech Recognition: {self.stt_type}")
        print(f"🔊 TTS Engine: {self.tts_type}")
        if VAD_ENABLED:
            print("🎚️  Voice Activity Detection: Enabled")
        if ENABLE_STREAMING:
            print("⚡ Streaming Responses: Enabled")
        
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Ready to listen!")
    
    def _initialize_wake_word(self):
        """Initialize wake word detection engine"""
        
        # Try Porcupine first (offline, accurate)
        if WAKE_WORD_ENGINE in ["auto", "porcupine"] and PORCUPINE_ACCESS_KEY:
            try:
                print("  Trying Porcupine wake word detection...")
                import pvporcupine
                from pvrecorder import PvRecorder
                
                # Check if we have a custom wake word file
                wake_word_file = self.personality.get("wake_word_file")
                
                if wake_word_file and os.path.exists(wake_word_file):
                    # Use custom wake word file
                    print(f"  Loading custom wake word: {os.path.basename(wake_word_file)}")
                    self.wake_engine = pvporcupine.create(
                        access_key=PORCUPINE_ACCESS_KEY,
                        keyword_paths=[wake_word_file],
                        sensitivities=[PORCUPINE_SENSITIVITY]
                    )
                    self.wake_type = "Porcupine (Custom Wake Word)"
                else:
                    # Try built-in keywords
                    wake_word_lower = self.wake_word.lower().replace(" ", "")
                    
                    # Check if it's a built-in keyword
                    builtin_keywords = list(pvporcupine.KEYWORDS)
                    matching_keyword = None
                    
                    for keyword in builtin_keywords:
                        if keyword.lower().replace(" ", "") == wake_word_lower:
                            matching_keyword = keyword
                            break
                    
                    if matching_keyword:
                        print(f"  Using built-in keyword: {matching_keyword}")
                        self.wake_engine = pvporcupine.create(
                            access_key=PORCUPINE_ACCESS_KEY,
                            keywords=[matching_keyword],
                            sensitivities=[PORCUPINE_SENSITIVITY]
                        )
                        self.wake_type = "Porcupine (Built-in Keyword)"
                    else:
                        print(f"  ⚠ No .ppn file found for '{self.wake_word}'")
                        print(f"  Available built-in keywords: {', '.join(builtin_keywords[:5])}...")
                        raise ValueError("Custom wake word file required")
                
                # Initialize audio recorder for Porcupine
                try:
                    # Use separate Porcupine microphone index if specified
                    if PORCUPINE_MICROPHONE_INDEX is not None:
                        self.porcupine_recorder = PvRecorder(
                            frame_length=self.wake_engine.frame_length,
                            device_index=PORCUPINE_MICROPHONE_INDEX
                        )
                        print(f"  ✓ Porcupine using microphone #{PORCUPINE_MICROPHONE_INDEX}")
                    else:
                        # Use default microphone
                        self.porcupine_recorder = PvRecorder(
                            frame_length=self.wake_engine.frame_length,
                            device_index=-1
                        )
                        print("  ✓ Porcupine using default microphone")
                    print("  ✓ Porcupine wake word detection loaded")
                    return
                except Exception as recorder_error:
                    # If specified mic fails, try default
                    if PORCUPINE_MICROPHONE_INDEX is not None:
                        print(f"  ⚠ Failed with Porcupine mic #{PORCUPINE_MICROPHONE_INDEX}, trying default...")
                        try:
                            self.porcupine_recorder = PvRecorder(
                                frame_length=self.wake_engine.frame_length,
                                device_index=-1
                            )
                            print("  ✓ Porcupine wake word detection loaded (default mic)")
                            return
                        except Exception:
                            pass
                    raise recorder_error
            
            except ImportError as e:
                print(f"  ⚠ Porcupine not available: {e}")
                print("  Install with: pip install pvporcupine pvrecorder")
            except Exception as e:
                print(f"  ⚠ Porcupine initialization failed: {e}")
        
        # Fallback to built-in (online via Google STT)
        self.wake_type = "Built-in (Online STT)"
        self.porcupine_recorder = None
        print("  ✓ Using built-in wake word detection")
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition engine"""
        
        # Try Whisper first (offline, accurate)
        if SPEECH_RECOGNITION_ENGINE in ["auto", "whisper"]:
            try:
                print("  Trying Whisper speech recognition...")
                import whisper
                
                self.stt_engine = whisper.load_model(WHISPER_MODEL, device=self.device)
                self.stt_type = f"Whisper ({WHISPER_MODEL}) - Offline"
                print(f"  ✓ Whisper {WHISPER_MODEL} model loaded")
                return
            
            except ImportError:
                print("  ⚠ Whisper not available (install: pip install openai-whisper)")
            except Exception as e:
                print(f"  ⚠ Whisper initialization failed: {e}")
        
        # Fallback to Google STT (online, free)
        self.stt_type = "Google STT (Online)"
        print("  ✓ Using Google Speech Recognition")
    
    def _initialize_vad(self):
        """Initialize Voice Activity Detection"""
        try:
            import webrtcvad
            self.vad_model = webrtcvad.Vad(VAD_SENSITIVITY)
            print("  ✓ Voice Activity Detection enabled")
        except ImportError:
            print("  ⚠ VAD not available (install: pip install webrtcvad)")
        except Exception as e:
            print(f"  ⚠ VAD initialization failed: {e}")
    
    def _initialize_tts(self):
        """Initialize TTS engine with fallback from Kokoro to KittenTTS"""
        
        # Try Kokoro first
        try:
            print("  Trying Kokoro TTS...")
            from kokoro import KPipeline
            
            lang = self.personality["voice"].get("language", "en-us")
            lang_map = {
                "en-us": "a", "en-gb": "a", "en": "a",
                "ja": "ja", "ko": "ko", "zh-cn": "zh"
            }
            kokoro_lang = lang_map.get(lang.lower(), "a")
            
            self.voice_name = self.personality["voice"].get("kokoro_voice", "af_sky")
            self.tts_engine = KPipeline(lang_code=kokoro_lang)
            self.tts_type = "Kokoro"
            print("  ✓ Kokoro TTS loaded successfully")
            return
            
        except ImportError as e:
            print(f"  ⚠ Kokoro not available: {e}")
        except Exception as e:
            print(f"  ⚠ Kokoro initialization failed: {e}")
        
        # Fallback to KittenTTS
        try:
            print("  Trying KittenTTS (fallback)...")
            from kittentts import KittenTTS
            
            self.tts_engine = KittenTTS("KittenML/kitten-tts-nano-0.1", device=self.device)
            self.tts_type = "KittenTTS"
            
            kokoro_voice = self.personality["voice"].get("kokoro_voice", "af_sky")
            self.kitten_voice = self._map_kokoro_to_kitten_voice(kokoro_voice)
            
            print("  ✓ KittenTTS loaded successfully")
            return
            
        except ImportError as e:
            print(f"  ⚠ KittenTTS not available: {e}")
        except Exception as e:
            print(f"  ⚠ KittenTTS initialization failed: {e}")
        
        raise RuntimeError(
            "❌ No TTS engine available!\n"
            "Install either:\n"
            "  - Kokoro: pip install kokoro>=0.9.4\n"
            "  - KittenTTS: pip install https://github.com/KittenML/KittenTTS/releases/download/0.1/kittentts-0.1.0-py3-none-any.whl"
        )
    
    def _map_kokoro_to_kitten_voice(self, kokoro_voice):
        """Map Kokoro voice names to KittenTTS voice IDs"""
        female_voices = {
            "af_sky": "2F", "af_bella": "1F", "af_sarah": "3F",
            "af_heart": "2F", "af_alloy": "3F", "af_nicole": "1F",
            "bf_emma": "4F",
        }
        male_voices = {
            "am_adam": "3M", "am_michael": "2M",
            "bm_lewis": "4M", "bm_george": "3M",
        }
        
        if kokoro_voice in female_voices:
            return female_voices[kokoro_voice]
        elif kokoro_voice in male_voices:
            return male_voices[kokoro_voice]
        else:
            return "2F"
    
    def get_random_response(self, response_type):
        """Get a random response from personality responses"""
        responses = self.personality["responses"].get(response_type, [""])
        return random.choice(responses)
    
    def detect_voice_activity(self, audio_data):
        """Detect if audio contains speech using VAD"""
        if not self.vad_model:
            return True  # Assume speech if VAD not available
        
        try:
            # VAD expects 16kHz audio in chunks
            is_speech = self.vad_model.is_speech(audio_data, 16000)
            return is_speech
        except Exception:
            return True
    
    def listen(self, listening_for_wake=False):
        """Capture audio from microphone and convert to text"""
        try:
            with self.microphone as source:
                if listening_for_wake:
                    print(f"\n💤 Sleeping... Say '{self.wake_word}' to wake me up", end="", flush=True)
                    # Lower energy threshold for wake word detection
                    self.recognizer.energy_threshold = 300
                else:
                    print("\n🎤 Listening...")
                    # Reset to a reasonable threshold for commands
                    self.recognizer.energy_threshold = 400
                
                # Longer timeout for wake word
                if listening_for_wake:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                else:
                    audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
                
            print("\r🔄 Processing speech...                                      ")
            
            # Use Whisper if available
            if self.stt_engine and self.stt_type.startswith("Whisper"):
                return self._transcribe_whisper(audio)
            else:
                return self._transcribe_google(audio)
            
        except sr.WaitTimeoutError:
            if not listening_for_wake:
                response = self.get_random_response("timeout")
                print(f"⏱️  {response}")
            return None
        except sr.UnknownValueError:
            if not listening_for_wake:
                response = self.get_random_response("error")
                print(f"❌ {response}")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None
    
    def _transcribe_whisper(self, audio):
        """Transcribe audio using Whisper"""
        try:
            # Convert audio bytes to float32 numpy (Whisper expects 16 kHz float32 mono)
            wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
            audio_np = np.frombuffer(wav_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # If multi-channel, make mono
            if audio_np.ndim > 1:
                audio_np = np.mean(audio_np, axis=1)

            # Quick silence check
            peak = float(np.abs(audio_np).max()) if audio_np.size else 0.0
            rms = float(np.sqrt(np.mean(audio_np ** 2))) if audio_np.size else 0.0
            print(f"  Audio RMS: {rms:.6f}, Peak: {peak:.6f}")
            if audio_np.size == 0 or peak < 1e-4 or rms < 1e-5:
                print("⚠️  No significant audio detected (silence)")
                return None

            # Use whisper's audio helpers to pad/trim to the model's expected length
            try:
                from whisper import audio as whisper_audio
                audio_np = whisper_audio.pad_or_trim(audio_np)
            except Exception:
                # If whisper.audio helpers aren't available, proceed with raw audio
                pass

            # Use config-selected fp16 flag
            result = self.stt_engine.transcribe(audio_np, fp16=self.use_fp16, language=self.personality.get("voice", {}).get("language", "en"))
            text = result.get("text", "").strip()

            if text:
                print(f"📝 You said: {text}")
                return text
            else:
                print("⚠️  No speech detected")
            return None

        except Exception as e:
            print(f"❌ Whisper transcription error: {e}")
            # Fallback to Google
            return self._transcribe_google(audio)

    def _start_interactive_tuner(self):
        """Start a background thread to accept simple runtime tuning commands from stdin.

        Commands:
          - vad <0-3>           : set VAD_SENSITIVITY
          - energy <value>      : set recognizer.energy_threshold
          - show                : show current settings
          - fp16 auto|true|false : set FP16_MODE at runtime
        """
        def tuner():
            print("Interactive tuner: type 'show', 'vad <0-3>', 'energy <value>' or 'fp16 <auto|true|false>'")
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    cmd = parts[0].lower()
                    if cmd == "show":
                        print(f"Device: {self.device}, fp16: {self.use_fp16}, VAD_SENSITIVITY: {cfg.VAD_SENSITIVITY}, energy_threshold: {self.recognizer.energy_threshold}")
                    elif cmd == "vad" and len(parts) > 1:
                        try:
                            new = int(parts[1])
                            cfg.VAD_SENSITIVITY = max(0, min(3, new))
                            self._initialize_vad()
                            print(f"Set VAD_SENSITIVITY = {cfg.VAD_SENSITIVITY}")
                        except Exception as ex:
                            print(f"Invalid vad value: {ex}")
                    elif cmd == "energy" and len(parts) > 1:
                        try:
                            new = int(parts[1])
                            self.recognizer.energy_threshold = new
                            print(f"Set energy_threshold = {self.recognizer.energy_threshold}")
                        except Exception as ex:
                            print(f"Invalid energy value: {ex}")
                    elif cmd == "fp16" and len(parts) > 1:
                        mode = parts[1].lower()
                        if mode in ("auto", "true", "false"):
                            cfg.FP16_MODE = mode
                            # Re-run device setup to recompute USE_FP16
                            cfg.setup_device()
                            self.use_fp16 = cfg.get_fp16()
                            print(f"Set FP16_MODE = {cfg.FP16_MODE}, use_fp16 = {self.use_fp16}")
                        else:
                            print("Invalid fp16 mode. Use auto|true|false")
                    else:
                        print("Unknown command. Use: show, vad <0-3>, energy <value>, fp16 <auto|true|false>")
                except Exception as e:
                    print(f"Tuner error: {e}")
                    break

        thread = threading.Thread(target=tuner, daemon=True, name="interactive-tuner")
        thread.start()
    
    def _transcribe_google(self, audio):
        """Transcribe audio using Google STT"""
        try:
            lang = self.personality["voice"]["language"]
            text = self.recognizer.recognize_google(audio, language=lang)
            print(f"You said: {text}")
            return text
        except Exception as e:
            print(f"❌ Google STT error: {e}")
            return None
    
    def think(self, user_input):
        """Send text to Gemini and get response"""
        try:
            print("🤔 Thinking...")
            
            if ENABLE_STREAMING:
                return self._think_streaming(user_input)
            else:
                response = self.chat.send_message(user_input)
                reply = response.text
                print(f"Assistant: {reply}")
                return reply
        
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return "Sorry, I encountered an error processing your request."
    
    def _think_streaming(self, user_input):
        """Send text to Gemini and get streaming response"""
        try:
            response = self.chat.send_message(user_input, stream=True)
            
            full_response = []
            print("Assistant: ", end="", flush=True)
            
            for chunk in response:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    full_response.append(chunk.text)
            
            print()  # New line after streaming
            return "".join(full_response)
        
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            # Fallback to non-streaming
            response = self.chat.send_message(user_input)
            return response.text
    
    def speak(self, text, blocking=True):
        """Convert text to speech and play it"""
        def _speak_thread():
            try:
                print(f"🔊 Speaking with {self.tts_type}...")
                
                if self.tts_type == "Kokoro":
                    self._speak_kokoro(text)
                elif self.tts_type == "KittenTTS":
                    self._speak_kitten(text)
                else:
                    print("❌ No TTS engine available")
                    
            except Exception as e:
                print(f"❌ Text-to-speech error: {e}")
                import traceback
                traceback.print_exc()
        
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()
        
        if blocking:
            thread.join()
    
    def _speak_kokoro(self, text):
        """Generate speech using Kokoro TTS"""
        speed = self.personality["voice"].get("speed", "normal")
        speed_map = {"slow": 0.8, "normal": 1.0, "fast": 1.2}
        speed_value = speed_map.get(speed, 1.0)
        
        generator = self.tts_engine(text, voice=self.voice_name, speed=speed_value)
        
        for i, (graphemes, phonemes, audio_chunk) in enumerate(generator):
            if not isinstance(audio_chunk, np.ndarray):
                audio_chunk = np.array(audio_chunk, dtype=np.float32)
            
            # Use selected speaker if configured
            if SPEAKER_INDEX is not None:
                sd.play(audio_chunk, self.sample_rate, device=SPEAKER_INDEX)
            else:
                sd.play(audio_chunk, self.sample_rate)
            sd.wait()
    
    def _speak_kitten(self, text):
        """Generate speech using KittenTTS"""
        speed = self.personality["voice"].get("speed", "normal")
        
        audio = self.tts_engine.generate(text, voice=self.kitten_voice)
        
        if not isinstance(audio, np.ndarray):
            audio = np.array(audio, dtype=np.float32)
        
        if speed == "slow":
            audio = self._change_speed(audio, 0.85)
        elif speed == "fast":
            audio = self._change_speed(audio, 1.15)
        
        # Use selected speaker if configured
        if SPEAKER_INDEX is not None:
            sd.play(audio, self.sample_rate, device=SPEAKER_INDEX)
        else:
            sd.play(audio, self.sample_rate)
        sd.wait()
    
    def _change_speed(self, audio, speed_factor):
        """Change audio speed by resampling"""
        indices = np.round(np.arange(0, len(audio), speed_factor)).astype(int)
        indices = indices[indices < len(audio)]
        return audio[indices]
    
    def check_for_wake_word(self, text):
        """Check if the wake word is in the text"""
        return self.wake_word in text.lower()
    
    def listen_for_wake_word_porcupine(self):
        """Listen for wake word using Porcupine (frame-by-frame processing)"""
        try:
            if not self.porcupine_recorder.is_recording:
                self.porcupine_recorder.start()
            
            # Read audio frame
            pcm = self.porcupine_recorder.read()
            
            # Process with Porcupine
            keyword_index = self.wake_engine.process(pcm)
            
            # Return True if wake word detected
            return keyword_index >= 0
            
        except Exception as e:
            print(f"⚠️  Porcupine error: {e}")
            return False
    
    def run(self):
        """Main loop for the voice assistant"""
        print("\n" + "="*60)
        print(f"🎙️  {self.personality['name']} - Voice Assistant Started")
        print("="*60)
        print(f"💬 Wake word: '{self.wake_word}'")
        print("💤 Say 'sleep' to put me in standby mode")
        print("👋 Say 'exit', 'quit', or 'goodbye' to stop completely")
        
        if self.plugin_manager:
            plugins = self.plugin_manager.get_plugin_info()
            if plugins:
                print(f"🔌 Loaded {len(plugins)} plugin(s):")
                for plugin in plugins:
                    print(f"   - {plugin['name']}: {plugin['description']}")
        
        print("="*60 + "\n")
        
        try:
            while True:
                # If sleeping, listen for wake word
                if not self.is_awake:
                    # Use Porcupine if available
                    if self.wake_type.startswith("Porcupine") and self.porcupine_recorder:
                        print(f"\r💤 Sleeping... Say '{self.wake_word}' to wake me up", end="", flush=True)
                        
                        if self.listen_for_wake_word_porcupine():
                            print("\r" + " " * 70 + "\r", end="", flush=True)  # Clear line
                            self.is_awake = True
                            wake_response = self.get_random_response("wake_acknowledgment")
                            print(f"✨ {self.personality['name']}: {wake_response}")

                            # Speak the acknowledgement non-blocking so we can start
                            # preparing the recognizer immediately; then recalibrate
                            # for ambient noise so short commands (e.g. "what is the time")
                            # are more likely to be captured.
                            self.speak(wake_response, blocking=False)

                            # Give TTS a brief moment to start playing, then recalibrate
                            # the recognizer so ambient noise and playback are accounted for.
                            time.sleep(0.15)
                            try:
                                with self.microphone as source:
                                    # Short adjustment to be ready for user command
                                    self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                            except Exception:
                                # If recalibration fails, continue anyway
                                pass
                    else:
                        # Fallback to STT-based detection
                        user_input = self.listen(listening_for_wake=True)
                        
                        if user_input and self.check_for_wake_word(user_input):
                            self.is_awake = True
                            wake_response = self.get_random_response("wake_acknowledgment")
                            print(f"✨ {self.personality['name']}: {wake_response}")
                            self.speak(wake_response)
                            
                            # Reset energy threshold after wake word
                            with self.microphone as source:
                                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    continue
                
                # If awake, listen for commands
                user_input = self.listen()
                
                if user_input is None:
                    continue
                
                # Check for sleep command
                if "sleep" in user_input.lower() and len(user_input.split()) <= 3:
                    self.is_awake = False
                    sleep_msg = "Going to sleep mode. Wake me when you need me!"
                    print(f"💤 {self.personality['name']}: {sleep_msg}")
                    self.speak(sleep_msg)
                    continue
                
                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "goodbye", "stop"]:
                    farewell = self.get_random_response("farewell")
                    print(f"👋 {self.personality['name']}: {farewell}")
                    self.speak(farewell)
                    break
                
                # Try plugins first
                response = None
                if self.plugin_manager:
                    response = self.plugin_manager.process_input(user_input, {"personality": self.personality})
                
                # If no plugin handled it, use Gemini
                if not response:
                    response = self.think(user_input)
                
                # Speak the response
                self.speak(response)
        
        finally:
            # Cleanup Porcupine resources
            if self.porcupine_recorder and self.porcupine_recorder.is_recording:
                self.porcupine_recorder.stop()
            if self.porcupine_recorder:
                self.porcupine_recorder.delete()
            if self.wake_engine:
                self.wake_engine.delete()

def main():
    # Check if API key is set
    if not GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY not found!")
        print("Please create a .env file with your API key:")
        print("GEMINI_API_KEY=your_api_key_here")
        return
    
    # Check for personality argument
    import sys
    personality_path = None
    if len(sys.argv) > 1:
        personality_path = sys.argv[1]
        print(f"Loading personality from: {personality_path}")
    
    try:
        assistant = VoiceAssistant(personality_path)
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Assistant stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
