# Voice Assistant with Gemini - Full Featured Edition

A Python-based voice assistant with advanced features including offline wake word detection, local speech recognition, streaming responses, GPU acceleration, and an extensible plugin system!

## Features

### Core Features
- 🎤 **Speech Recognition** with dual engine support:
  - Whisper (offline, GPU-accelerated)
  - Google STT (online, free)
- 🤖 **AI Responses** powered by Google Gemini 2.5 Flash
- 🔊 **Dual TTS System** with automatic fallback:
  - Kokoro TTS (primary) - High quality, 50+ voices
  - KittenTTS (fallback) - Ultra-lightweight, <25MB
- 💬 **Conversational Context** (remembers chat history)
- 🎭 **Swappable Personality System** with JSON configs

### Advanced Features
- 🎯 **Offline Wake Word Detection** using Porcupine
- ⚡ **Streaming Responses** from Gemini (see responses in real-time)
- 🎙️ **Local Speech Recognition** with Whisper (works offline)
- 🎚️ **Voice Activity Detection** for better speech capture
- 🖥️ **GPU Acceleration** for Whisper and TTS
- 🔌 **Plugin System** for extensibility
- 💤 **Sleep Mode** to save resources
- 🎵 **Multiple Voice Options** per personality

## Prerequisites

- Python 3.10 or higher (3.10-3.12 recommended)
- Microphone access
- Internet connection (for Gemini AI and online features)
- Google Gemini API key
- **Optional**: NVIDIA GPU for acceleration

## Installation

### Step 1: Core Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: TTS Engine (Required)

Install at least one TTS engine:

```bash
# Kokoro (recommended - high quality)
pip install kokoro>=0.9.4

# Install espeak-ng (required by Kokoro)
# Windows: Download from https://github.com/espeak-ng/espeak-ng/releases
# macOS: brew install espeak-ng
# Linux: sudo apt-get install espeak-ng

# KittenTTS (fallback - lightweight)
pip install https://github.com/KittenML/KittenTTS/releases/download/0.1/kittentts-0.1.0-py3-none-any.whl
```

### Step 3: Optional Features

```bash
# Offline Wake Word Detection (Porcupine)
pip install pvporcupine
# Get free access key: https://picovoice.ai/console/

# Local Speech Recognition (Whisper)
pip install openai-whisper torch torchaudio

# Voice Activity Detection
pip install webrtcvad

# Plugin Dependencies
pip install requests  # For weather plugin
```

### Step 4: Configuration

1. Copy `.env.example` to `.env`
2. Add your Gemini API key
3. Configure optional features

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Wake Word Detection
WAKE_WORD_ENGINE=auto  # auto, porcupine, builtin
PORCUPINE_ACCESS_KEY=your_key  # From picovoice.ai
PORCUPINE_SENSITIVITY=0.5  # 0.0-1.0

# Speech Recognition
SPEECH_RECOGNITION_ENGINE=auto  # auto, whisper, google
WHISPER_MODEL=base  # tiny, base, small, medium, large

# Voice Activity Detection
VAD_ENABLED=true
VAD_SENSITIVITY=3  # 0-3, higher = more sensitive

# GPU Configuration
USE_GPU=auto  # auto, true, false

# Features
ENABLE_STREAMING=true
PLUGINS_ENABLED=true
```

## Usage

### Basic Usage

```bash
# Run with default personality
python main.py

# Run with specific personality
python main.py personalities/pirate.json
```

### Voice Commands

- **Wake**: Say the wake word (e.g., "hey spark")
- **Sleep**: Say "sleep" to enter standby mode
- **Exit**: Say "exit", "quit", or "goodbye" to stop

### Plugin Commands

The assistant comes with built-in plugins:

- **Weather**: "What's the weather in London?"
- **Time**: "What time is it?" or "What's the date?"
- **Calculator**: "What is 25 times 4?"
- **Audio**: "list microphones", "test speakers", "test audio"

### Audio Setup

If the assistant doesn't recognize your voice or you can't hear responses:

```bash
# Complete audio setup wizard (RECOMMENDED)
python tools/audio_setup.py

# Quick microphone test
python tools/test_microphone.py

# Or use the plugin while assistant is running
# Say: "list microphones", "test speakers", or "test audio"
```

The setup wizard will help you:
- Find working microphone and speakers
- Test audio loopback (speaker → mic)
- Automatically save configuration

## Feature Deep Dive

### 1. Offline Wake Word Detection (Porcupine)

**Benefits**:
- ⚡ Works offline - no internet needed
- 🎯 More accurate than keyword matching
- 🔋 Lower CPU usage
- 🔒 Privacy - audio never leaves device
- 🎭 **Custom wake words per personality**

**Setup**:
1. Get free access key from https://picovoice.ai/console/
2. Add to `.env`: `PORCUPINE_ACCESS_KEY=your_key`
3. Set `WAKE_WORD_ENGINE=porcupine`
4. Install: `pip install pvporcupine pvrecorder`

**Custom Wake Words**:

Each personality can have its own unique wake word! 

1. **Create** your wake word at [Picovoice Console](https://console.picovoice.ai/)
2. **Download** the `.ppn` file for your platform
3. **Place** in `wake_words/` directory:
   ```
   wake_words/
   ├── hey_spark/
   │   └── Hey-Spark_en_windows_v3_0_0.ppn
   └── jarvis/
       └── Jarvis_en_windows_v3_0_0.ppn
   ```
4. **Configure** in personality JSON:
   ```json
   {
     "name": "Spark",
     "wake_word": "hey spark",
     "wake_word_file": "wake_words/hey_spark/Hey-Spark_en_windows_v3_0_0.ppn"
   }
   ```

**Built-in Keywords** (no custom file needed):
- alexa, computer, jarvis, hey google, ok google, picovoice, porcupine, and more

See `wake_words/README.md` and `WAKE_WORD_SETUP.md` for detailed instructions.

**Fallback**: If Porcupine unavailable, uses built-in detection

### 2. Streaming Responses

**Benefits**:
- ⚡ See responses as they're generated
- 🚀 Feels more responsive
- 💬 Better for long responses

**How it works**:
- Gemini streams response chunks in real-time
- Text appears progressively instead of all at once
- Automatically enabled when `ENABLE_STREAMING=true`

### 3. Local Speech Recognition (Whisper)

**Benefits**:
- 🔒 Works completely offline
- 🎯 More accurate than Google STT
- 🌍 Supports 99 languages
- 🖥️ GPU accelerated

**Models**:
- `tiny` - 39M params, fastest, least accurate
- `base` - 74M params, good balance (recommended)
- `small` - 244M params, better accuracy
- `medium` - 769M params, high accuracy
- `large` - 1550M params, best accuracy

**GPU vs CPU**:
```
Model: base
CPU: ~1.5s per utterance
GPU: ~0.3s per utterance
```

**Fallback**: Uses Google STT if Whisper unavailable

### 4. Voice Activity Detection (VAD)

**Benefits**:
- 🎤 Better speech detection
- 🔇 Filters background noise
- ⚡ Faster response times

**How it works**:
- Uses WebRTC VAD engine
- Detects when you start/stop speaking
- Reduces false triggers

**Sensitivity Levels**:
- `0` - Least aggressive (noisy environments)
- `1` - Low aggressive
- `2` - Moderate (default)
- `3` - Most aggressive (quiet environments)

### 5. GPU Acceleration

**Supported Operations**:
- Whisper speech recognition
- KittenTTS inference

**Auto-detection**:
```python
USE_GPU=auto  # Automatically uses GPU if available
```

**Check GPU usage**:
```bash
# On startup, you'll see:
🖥️  Using device: CUDA
✓ GPU detected: NVIDIA GeForce RTX 3080
```

**Performance Boost**:
- Whisper: 5-10x faster
- KittenTTS: 2-3x faster

### 6. Plugin System

**Creating Custom Plugins**:

```python
# plugins/my_plugin.py
from plugins import Plugin

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.description = "My custom plugin"
        self.triggers = ["trigger", "keyword"]
    
    def execute(self, user_input, context):
        # Your plugin logic here
        return "Plugin response"
```

**Built-in Plugins**:
- `weather.py` - Weather information
- `time.py` - Time and date
- `calculator.py` - Mathematical calculations
- `audio.py` - Audio device testing and configuration

**Plugin Features**:
- Auto-discovery (just add to plugins/ folder)
- Priority over Gemini for matching triggers
- Access to conversation context
- Can return None to defer to Gemini

## Architecture

### Component Flow

```
Microphone → VAD → Speech Recognition (Whisper/Google)
                         ↓
                   Wake Word Detection
                         ↓
                   Plugin System
                         ↓
                   Gemini AI (streaming)
                         ↓
                   TTS (Kokoro/KittenTTS)
                         ↓
                   Speakers
```

### Engine Selection Logic

Each component tries the best option first, then falls back:

1. **Wake Word**: Porcupine (offline) → Built-in (online)
2. **Speech Recognition**: Whisper (offline) → Google (online)
3. **TTS**: Kokoro (quality) → KittenTTS (lightweight)
4. **Response**: Plugins → Gemini AI

## Performance Comparison

### Speech Recognition

| Engine | Speed | Accuracy | Offline | GPU |
|--------|-------|----------|---------|-----|
| Whisper (tiny) | ⚡⚡⚡ | ⭐⭐⭐ | ✅ | ✅ |
| Whisper (base) | ⚡⚡ | ⭐⭐⭐⭐ | ✅ | ✅ |
| Whisper (small) | ⚡ | ⭐⭐⭐⭐⭐ | ✅ | ✅ |
| Google STT | ⚡⚡⚡ | ⭐⭐⭐⭐ | ❌ | ❌ |

### Wake Word Detection

| Engine | Accuracy | CPU | Offline |
|--------|----------|-----|---------|
| Porcupine | ⭐⭐⭐⭐⭐ | Low | ✅ |
| Built-in | ⭐⭐⭐ | Medium | ❌ |

## Troubleshooting

### GPU Not Detected

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Porcupine Wake Word Issues

- Verify access key is correct
- Check internet connection (first run downloads model)
- Ensure microphone permissions are granted
- Try adjusting `PORCUPINE_SENSITIVITY`

### Whisper Transcription Slow

- Use smaller model (`tiny` or `base`)
- Enable GPU acceleration
- Check `USE_GPU=true` in .env

### Plugins Not Loading

```bash
# Check plugin syntax
python -c "from plugins import PluginManager; pm = PluginManager(); print(pm.get_plugin_info())"

# Verify plugins directory exists
ls -la plugins/
```

### Audio Issues

```bash
# Complete audio setup (RECOMMENDED)
python tools/audio_setup.py

# Quick microphone test
python tools/test_microphone.py

# Test with speech_recognition
python -m speech_recognition

# Manual speaker test
python -c "import sounddevice as sd; import numpy as np; sd.play(np.random.randn(44100), 44100); sd.wait()"
```

## Platform-Specific Notes

### Windows

```bash
# PyAudio may need manual installation
# Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

# espeak-ng
choco install espeak-ng

# CUDA (for GPU)
# Download from: https://developer.nvidia.com/cuda-downloads
```

### macOS

```bash
# Install dependencies
brew install portaudio espeak-ng

# M1/M2 Macs (Apple Silicon)
# Use MPS backend for GPU acceleration
USE_GPU=false  # CUDA not available, use CPU
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev espeak-ng python3-pyaudio

# NVIDIA GPU
sudo apt-get install nvidia-cuda-toolkit
```

## Resource Usage

### Minimal Configuration
- RAM: ~500MB
- Storage: ~200MB
- Components: KittenTTS, Google STT, Built-in wake word

### Full Configuration
- RAM: ~2GB (CPU) / ~4GB (GPU)
- Storage: ~5GB (Whisper models)
- Components: All features enabled

### Recommended for Raspberry Pi
```bash
SPEECH_RECOGNITION_ENGINE=google
USE_GPU=false
WHISPER_MODEL=tiny  # If using Whisper
WAKE_WORD_ENGINE=porcupine  # Lightweight
```

## API Keys

### Gemini API (Required)
- Free tier: 60 requests/minute
- Get key: https://makersuite.google.com/app/apikey

### Porcupine (Optional)
- Free tier: 3 wake words, unlimited usage
- Get key: https://picovoice.ai/console/

## Future Enhancements

- [ ] Voice cloning with your own voice
- [ ] Multi-language support in personalities
- [ ] Background music/sound effects
- [ ] Web interface for remote control
- [ ] Mobile app integration
- [ ] Custom Porcupine wake word training
- [ ] Emotion detection in voice
- [ ] Multi-user support
- [ ] Home automation integration

## Contributing

Contributions welcome! Areas of interest:
- New plugins (smart home, music, news, etc.)
- Additional TTS engines
- Performance optimizations
- Documentation improvements

## Credits

- **Kokoro TTS** by hexgrad
- **KittenTTS** by KittenML
- **Whisper** by OpenAI
- **Porcupine** by Picovoice
- **Google Gemini** for AI responses

## License

MIT

## Resources

- **Kokoro**: https://github.com/hexgrad/kokoro
- **KittenTTS**: https://github.com/KittenML/KittenTTS
- **Whisper**: https://github.com/openai/whisper
- **Porcupine**: https://picovoice.ai/platform/porcupine/
- **Gemini API**: https://ai.google.dev/
