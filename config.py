import os
import json
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# Audio Configuration
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
AUDIO_FORMAT = "mp3"

# Microphone selection
MICROPHONE_INDEX = os.getenv("MICROPHONE_INDEX", None)
if MICROPHONE_INDEX is not None:
    MICROPHONE_INDEX = int(MICROPHONE_INDEX)

# Porcupine microphone selection (may differ from MICROPHONE_INDEX)
PORCUPINE_MICROPHONE_INDEX = os.getenv("PORCUPINE_MICROPHONE_INDEX", None)
if PORCUPINE_MICROPHONE_INDEX is not None and PORCUPINE_MICROPHONE_INDEX != "":
    PORCUPINE_MICROPHONE_INDEX = int(PORCUPINE_MICROPHONE_INDEX)
else:
    PORCUPINE_MICROPHONE_INDEX = None

# Speaker selection
SPEAKER_INDEX = os.getenv("SPEAKER_INDEX", None)
if SPEAKER_INDEX is not None:
    SPEAKER_INDEX = int(SPEAKER_INDEX)

# Personality Configuration
PERSONALITY_FILE = os.getenv("PERSONALITY_FILE", "personalities/default.json")

# Wake Word Detection Configuration
WAKE_WORD_ENGINE = os.getenv("WAKE_WORD_ENGINE", "auto")  # auto, porcupine, builtin
PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")
PORCUPINE_SENSITIVITY = float(os.getenv("PORCUPINE_SENSITIVITY", "0.5"))
WAKE_WORDS_DIR = "wake_words"  # Directory containing .ppn wake word files

# Speech Recognition Configuration
SPEECH_RECOGNITION_ENGINE = os.getenv("SPEECH_RECOGNITION_ENGINE", "auto")  # auto, whisper, google
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large

# Voice Activity Detection
VAD_ENABLED = os.getenv("VAD_ENABLED", "true").lower() == "true"
VAD_SENSITIVITY = int(os.getenv("VAD_SENSITIVITY", "3"))  # 0-3, higher = more sensitive

# GPU Configuration
USE_GPU = os.getenv("USE_GPU", "auto")  # auto, true, false
DEVICE = None  # Will be set based on GPU availability

# Streaming Configuration
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"

# Plugin Configuration
PLUGINS_ENABLED = os.getenv("PLUGINS_ENABLED", "true").lower() == "true"
PLUGINS_DIR = "plugins"

def find_wake_word_file(wake_word_text):
    """Find the .ppn file for a given wake word text"""
    import glob
    
    # Normalize wake word text for matching
    normalized = wake_word_text.lower().replace(" ", "-")
    
    # Search for matching .ppn files
    pattern = os.path.join(WAKE_WORDS_DIR, "**", f"*{normalized}*.ppn")
    matches = glob.glob(pattern, recursive=True)
    
    if matches:
        return matches[0]  # Return first match
    
    # Try without normalization
    pattern = os.path.join(WAKE_WORDS_DIR, "**", "*.ppn")
    all_ppn_files = glob.glob(pattern, recursive=True)
    
    for ppn_file in all_ppn_files:
        filename = os.path.basename(ppn_file).lower()
        if wake_word_text.lower().replace(" ", "") in filename.replace("-", "").replace("_", ""):
            return ppn_file
    
    return None

def load_personality(personality_path=None):
    """Load personality configuration from JSON file"""
    path = personality_path or PERSONALITY_FILE
    try:
        with open(path, 'r', encoding='utf-8') as f:
            personality = json.load(f)
        
        # Find wake word file if using Porcupine
        if "wake_word" in personality:
            wake_word_file = find_wake_word_file(personality["wake_word"])
            personality["wake_word_file"] = wake_word_file
            
            if wake_word_file:
                print(f"✓ Found wake word file: {wake_word_file}")
            else:
                print(f"⚠️  No .ppn file found for wake word: '{personality['wake_word']}'")
                print(f"   Place custom wake word files in: {WAKE_WORDS_DIR}/")
        
        return personality
        
    except FileNotFoundError:
        print(f"⚠️  Personality file not found: {path}")
        print("Using default personality...")
        return {
            "name": "Assistant",
            "wake_word": "hey assistant",
            "wake_word_file": None,
            "voice": {"language": "en-us", "speed": "normal", "kokoro_voice": "af_sky"},
            "system_prompt": "You are a helpful AI assistant.",
            "responses": {
                "wake_acknowledgment": ["Yes, I'm listening!"],
                "farewell": ["Goodbye!"],
                "error": ["Sorry, I didn't catch that."],
                "timeout": ["I'm here when you're ready."]
            }
        }
    except json.JSONDecodeError as e:
        print(f"⚠️  Error parsing personality file: {e}")
        print("Using default personality...")
        return load_personality()

def setup_device():
    """Setup computation device (CPU/GPU)"""
    global DEVICE
    
    if USE_GPU == "false":
        DEVICE = "cpu"
        return DEVICE
    
    try:
        import torch
        if torch.cuda.is_available() and USE_GPU in ["auto", "true"]:
            DEVICE = "cuda"
            print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
        else:
            DEVICE = "cpu"
            if USE_GPU == "true":
                print("⚠ GPU requested but not available, using CPU")
    except ImportError:
        DEVICE = "cpu"
        if USE_GPU == "true":
            print("⚠ PyTorch not installed, GPU support unavailable")
    
    return DEVICE

def get_device():
    """Get current device"""
    global DEVICE
    if DEVICE is None:
        return setup_device()
    return DEVICE
