# Custom Wake Words

This directory contains custom wake word files (`.ppn`) for Porcupine wake word detection.

## How to Add Custom Wake Words

### 1. Create Your Wake Word

Visit [Picovoice Console](https://console.picovoice.ai/) and:
- Sign up for a free account
- Go to "Porcupine" section
- Click "Create Wake Word"
- Enter your wake word phrase (e.g., "Hey Spark", "Computer", "Jarvis")
- Train the model

### 2. Download the Wake Word File

- After training, download the `.ppn` file for your platform:
  - **Windows**: `*_windows_*.ppn`
  - **Linux**: `*_linux_*.ppn`
  - **macOS**: `*_mac_*.ppn`
  - **Raspberry Pi**: `*_raspberry-pi_*.ppn`

### 3. Organize the File

Create a subdirectory for your wake word and place the `.ppn` file inside:

```
wake_words/
├── hey_spark/
│   └── Hey-Spark_en_windows_v3_0_0.ppn
├── jarvis/
│   └── Jarvis_en_windows_v3_0_0.ppn
└── computer/
    └── Computer_en_windows_v3_0_0.ppn
```

### 4. Configure Your Personality

In your personality JSON file (e.g., `personalities/default.json`), add the wake word configuration:

```json
{
  "name": "Spark",
  "wake_word": "hey spark",
  "wake_word_file": "wake_words/hey_spark/Hey-Spark_en_windows_v3_0_0.ppn",
  "voice": {
    "language": "en-us",
    "speed": "normal",
    "kokoro_voice": "af_sky"
  },
  ...
}
```

**Note:** The `wake_word_file` field is optional. If not specified, the system will:
1. Try to auto-detect a matching `.ppn` file based on the `wake_word` text
2. Fall back to built-in Porcupine keywords if available
3. Use online speech recognition as a last resort

### 5. Set Your Access Key

Make sure you have your Porcupine access key in `.env`:

```env
PORCUPINE_ACCESS_KEY=your_access_key_here
```

Get your free access key from [Picovoice Console](https://console.picovoice.ai/).

## Multiple Personalities with Different Wake Words

You can create multiple personalities, each with their own wake word:

**personalities/spark.json:**
```json
{
  "name": "Spark",
  "wake_word": "hey spark",
  "wake_word_file": "wake_words/hey_spark/Hey-Spark_en_windows_v3_0_0.ppn"
}
```

**personalities/jarvis.json:**
```json
{
  "name": "Jarvis",
  "wake_word": "jarvis",
  "wake_word_file": "wake_words/jarvis/Jarvis_en_windows_v3_0_0.ppn"
}
```

Then run with:
```bash
python main.py personalities/spark.json
# or
python main.py personalities/jarvis.json
```

## Sensitivity Tuning

Adjust wake word sensitivity in `.env`:

```env
PORCUPINE_SENSITIVITY=0.5
```

- **Lower (0.0-0.4)**: Fewer false alarms, may miss some detections
- **Medium (0.5)**: Balanced (recommended)
- **Higher (0.6-1.0)**: More sensitive, may have false positives

## Troubleshooting

### Wake word not detected
- Check that the `.ppn` file path is correct
- Increase `PORCUPINE_SENSITIVITY` in `.env`
- Speak clearly and at normal volume
- Ensure microphone is working (run `python tools/audio_setup.py`)

### Too many false detections
- Decrease `PORCUPINE_SENSITIVITY` in `.env`
- Train a more unique wake word phrase

### "No .ppn file found" error
- Verify the file exists at the specified path
- Check that the filename matches your platform (windows/linux/mac)
- Ensure the path in personality JSON is correct

## Built-in Keywords

Porcupine includes some built-in keywords that don't require custom `.ppn` files:
- alexa
- americano
- blueberry
- bumblebee
- computer
- grapefruit
- grasshopper
- hey google
- hey siri
- jarvis
- ok google
- picovoice
- porcupine
- terminator

To use a built-in keyword, just set the `wake_word` in your personality JSON (no `wake_word_file` needed).
