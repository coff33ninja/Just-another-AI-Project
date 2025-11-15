# Voice Assistant Tools

Utility scripts for testing and configuring the voice assistant.

## Available Tools

### audio_setup.py (Recommended)
**Complete audio setup wizard** - Configure both microphone and speakers.

```bash
python tools/audio_setup.py
```

This interactive wizard will:
- List all audio devices (inputs and outputs)
- Test speakers by playing tones
- Test microphones with speech recognition
- Run loopback test (speaker → microphone)
- Automatically save working configuration to `.env`

**Use this first if you're having audio issues!**

### test_microphone.py
Quick microphone diagnostic tool.

```bash
python tools/test_microphone.py
```

This will:
- List all available microphones
- Test audio capture with your default microphone
- Try transcription with Whisper and Google STT
- Show energy threshold levels

### select_microphone.py
Interactive microphone selector (microphone only).

```bash
python tools/select_microphone.py
```

This will:
- Show all input microphones
- Let you test each one individually
- Automatically save the working microphone to `.env`

## Using the Audio Plugin

You can also test audio from within the voice assistant:

1. Start the assistant: `python main.py`
2. Wake it up: "hey spark"
3. Say one of:
   - "list microphones" - Show input devices
   - "test microphone" - Test current microphone
   - "list speakers" - Show output devices
   - "test speakers" - Play test tone
   - "test audio" - Full loopback test

The plugin provides basic audio diagnostics without leaving the assistant.

## Troubleshooting

### No sound from speakers
1. Run `python tools/audio_setup.py`
2. Test each speaker until you hear the tone
3. Save the working speaker index

### Microphone not picking up voice
1. Run `python tools/audio_setup.py`
2. Test each microphone by speaking
3. Check energy threshold (should be 100-500)
4. Save the working microphone index

### Assistant doesn't wake up
1. Check microphone is working: `python tools/test_microphone.py`
2. Speak louder and clearer
3. Try a different microphone
4. Lower `PORCUPINE_SENSITIVITY` in `.env` (if using Porcupine)
