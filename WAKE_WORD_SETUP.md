# Wake Word Setup Guide

## What Changed

Your voice assistant now properly supports **custom wake words** using Porcupine! Each personality can have its own unique wake word.

## Key Updates

### 1. **Proper Porcupine Integration**
- Now uses `keyword_paths` parameter for custom `.ppn` files (not `keywords`)
- Uses `pvrecorder` for frame-by-frame audio processing
- Detects wake words offline with high accuracy

### 2. **Per-Personality Wake Words**
Each personality JSON can specify its own wake word:

```json
{
  "name": "Spark",
  "wake_word": "hey spark",
  "wake_word_file": "wake_words/hey_spark/Hey-Spark_en_windows_v3_0_0.ppn"
}
```

### 3. **Auto-Detection**
If you don't specify `wake_word_file`, the system will:
1. Search for matching `.ppn` files in `wake_words/` directory
2. Try built-in Porcupine keywords
3. Fall back to online speech recognition

## How to Use

### Current Setup (Hey Spark)

Your "Hey Spark" wake word is already configured! Just install the required packages:

```bash
pip install pvporcupine pvrecorder
```

Then run:
```bash
python main.py
```

### Adding More Wake Words

1. **Create wake word** at [Picovoice Console](https://console.picovoice.ai/)
2. **Download** the `.ppn` file for Windows
3. **Extract** to `wake_words/` directory:
   ```
   wake_words/
   ├── hey_spark/
   │   └── Hey-Spark_en_windows_v3_0_0.ppn
   └── jarvis/
       └── Jarvis_en_windows_v3_0_0.ppn
   ```

4. **Create personality** (e.g., `personalities/jarvis.json`):
   ```json
   {
     "name": "Jarvis",
     "wake_word": "jarvis",
     "wake_word_file": "wake_words/jarvis/Jarvis_en_windows_v3_0_0.ppn",
     "voice": {
       "language": "en-us",
       "speed": "normal",
       "kokoro_voice": "am_adam"
     },
     "system_prompt": "You are Jarvis, a sophisticated AI assistant..."
   }
   ```

5. **Run with personality**:
   ```bash
   python main.py personalities/jarvis.json
   ```

## Configuration Options

### .env Settings

```env
# Wake Word Engine
WAKE_WORD_ENGINE=porcupine  # auto, porcupine, or builtin

# Porcupine Access Key (get from console.picovoice.ai)
PORCUPINE_ACCESS_KEY=your_key_here

# Sensitivity (0.0 = fewer false alarms, 1.0 = more sensitive)
PORCUPINE_SENSITIVITY=0.5
```

### Sensitivity Tuning

- **0.3-0.4**: Very few false alarms, may miss some detections
- **0.5**: Balanced (recommended)
- **0.6-0.7**: More sensitive, catches more but may have false positives
- **0.8-1.0**: Very sensitive, higher false alarm rate

## Built-in Keywords

Porcupine includes these keywords (no custom file needed):
- alexa
- computer
- jarvis
- hey google
- ok google
- picovoice
- porcupine
- And more...

To use a built-in keyword, just set `wake_word` in your personality (no `wake_word_file` needed).

## Troubleshooting

### "No .ppn file found"
- Check the file path in your personality JSON
- Verify the file exists in `wake_words/` directory
- Make sure you downloaded the Windows version

### Wake word not detected
- Increase `PORCUPINE_SENSITIVITY` in `.env`
- Speak clearly at normal volume
- Check microphone with `python tools/audio_setup.py`
- Verify access key is correct

### Too many false detections
- Decrease `PORCUPINE_SENSITIVITY`
- Train a more unique wake word phrase
- Reduce background noise

### Import errors
```bash
pip install pvporcupine pvrecorder
```

## How It Works

### Before (Your Old Code)
```python
# Tried to use text-based keywords (only works for built-ins)
porcupine = pvporcupine.create(
    access_key=key,
    keywords=["hey spark"]  # ❌ Doesn't work for custom wake words
)
```

### After (New Code)
```python
# Uses custom .ppn file path
porcupine = pvporcupine.create(
    access_key=key,
    keyword_paths=["wake_words/hey_spark/Hey-Spark_en_windows_v3_0_0.ppn"]  # ✅ Correct!
)

# Frame-by-frame processing
recorder = PvRecorder(frame_length=porcupine.frame_length)
recorder.start()

while True:
    pcm = recorder.read()
    keyword_index = porcupine.process(pcm)
    if keyword_index >= 0:
        print("Wake word detected!")
```

## Example: Multiple Personalities

**personalities/spark.json** (Energetic assistant)
```json
{
  "name": "Spark",
  "wake_word": "hey spark",
  "wake_word_file": "wake_words/hey_spark/Hey-Spark_en_windows_v3_0_0.ppn",
  "voice": {"kokoro_voice": "af_sky"}
}
```

**personalities/jarvis.json** (Professional assistant)
```json
{
  "name": "Jarvis",
  "wake_word": "jarvis",
  "wake_word_file": "wake_words/jarvis/Jarvis_en_windows_v3_0_0.ppn",
  "voice": {"kokoro_voice": "am_adam"}
}
```

Switch between them:
```bash
python main.py personalities/spark.json
python main.py personalities/jarvis.json
```

## Next Steps

1. **Install dependencies**: `pip install pvporcupine pvrecorder`
2. **Test current setup**: `python main.py`
3. **Create more wake words** at [Picovoice Console](https://console.picovoice.ai/)
4. **Build multiple personalities** with unique wake words!

See `wake_words/README.md` for detailed instructions on creating custom wake words.
