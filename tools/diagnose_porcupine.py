#!/usr/bin/env python3
"""
Comprehensive Porcupine Wake Word Diagnostics
Helps identify why wake words aren't being detected
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

def check_dependencies():
    """Check if required packages are installed"""
    print("\n" + "="*70)
    print("🔍 CHECKING DEPENDENCIES")
    print("="*70)
    
    required = {
        'pvporcupine': 'pvporcupine',
        'pvrecorder': 'pvrecorder',
    }
    
    missing = []
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - MISSING")
            missing.append(package_name)
    
    if missing:
        print(f"\n❌ Install missing packages with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All dependencies installed")
    return True

def check_access_key():
    """Check if Porcupine access key is configured"""
    print("\n" + "="*70)
    print("🔑 CHECKING ACCESS KEY")
    print("="*70)
    
    load_dotenv()
    access_key = os.getenv("PORCUPINE_ACCESS_KEY", "").strip()
    
    if not access_key:
        print("✗ PORCUPINE_ACCESS_KEY not set in .env")
        print("\nHow to fix:")
        print("  1. Go to https://console.picovoice.ai/")
        print("  2. Sign up for a free account")
        print("  3. Copy your Access Key")
        print("  4. Add to .env: PORCUPINE_ACCESS_KEY=your_key_here")
        return False
    
    if len(access_key) < 10:
        print(f"✗ PORCUPINE_ACCESS_KEY appears invalid (too short): {access_key[:5]}...")
        return False
    
    print(f"✓ Access key configured: {access_key[:10]}...{access_key[-5:]}")
    return True

def check_wake_word_file():
    """Check if wake word .ppn file exists"""
    print("\n" + "="*70)
    print("📁 CHECKING WAKE WORD FILES")
    print("="*70)
    
    wake_words_dir = Path("wake_words")
    
    if not wake_words_dir.exists():
        print(f"✗ Directory not found: {wake_words_dir}")
        print("\nYou need custom .ppn wake word files. Create them at:")
        print("  https://console.picovoice.ai/")
        return False
    
    ppn_files = list(wake_words_dir.glob("**/*.ppn"))
    
    if not ppn_files:
        print(f"✗ No .ppn files found in {wake_words_dir}/")
        print("\nHow to fix:")
        print("  1. Go to https://console.picovoice.ai/")
        print("  2. Create a wake word (e.g., 'Hey Spark')")
        print("  3. Download the Windows .ppn file")
        print("  4. Place in wake_words/hey_spark/ directory")
        return False
    
    print(f"✓ Found {len(ppn_files)} .ppn file(s):")
    for ppn_file in ppn_files:
        size_kb = ppn_file.stat().st_size / 1024
        print(f"   - {ppn_file.relative_to('.')} ({size_kb:.1f} KB)")
        
        # Verify it's a valid Porcupine file
        if not ppn_file.name.endswith('_v3_0_0.ppn'):
            print(f"     ⚠️  Filename pattern unusual (expected *_v3_0_0.ppn)")
    
    return True

def check_personality_config():
    """Check personality file configuration"""
    print("\n" + "="*70)
    print("⚙️  CHECKING PERSONALITY CONFIGURATION")
    print("="*70)
    
    personality_file = Path("personalities/default.json")
    
    if not personality_file.exists():
        print(f"✗ Personality file not found: {personality_file}")
        return False
    
    try:
        with open(personality_file, 'r') as f:
            personality = json.load(f)
        
        print(f"✓ Personality: {personality.get('name', 'Unknown')}")
        print(f"  Wake word: '{personality.get('wake_word', 'NOT SET')}'")
        
        wake_word_file = personality.get('wake_word_file')
        if not wake_word_file:
            print(f"  ⚠️  wake_word_file not set (will auto-detect)")
            return True
        
        if not Path(wake_word_file).exists():
            print(f"  ✗ wake_word_file not found: {wake_word_file}")
            return False
        
        print(f"  ✓ wake_word_file: {wake_word_file}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in {personality_file}: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading {personality_file}: {e}")
        return False

def check_microphone():
    """Check microphone availability"""
    print("\n" + "="*70)
    print("🎤 CHECKING MICROPHONE")
    print("="*70)
    
    load_dotenv()
    
    try:
        from pvrecorder import PvRecorder
        
        devices = PvRecorder.get_available_devices()
        print(f"✓ Found {len(devices)} audio device(s):")
        for i, device in enumerate(devices):
            print(f"   [{i}] {device}")
        
        if len(devices) == 0:
            print("✗ No audio devices found!")
            return False
        
        # Test default device
        print("\n  Testing default microphone...")
        try:
            recorder = PvRecorder(device_index=-1, frame_length=512)
            print("  ✓ Default microphone works")
            recorder.delete()
        except Exception as e:
            print(f"  ✗ Default microphone failed: {e}")
            return False
        
        # Test configured device if specified
        mic_index = os.getenv("MICROPHONE_INDEX")
        if mic_index and mic_index != "":
            mic_index = int(mic_index)
            print(f"\n  Testing configured microphone #{mic_index}...")
            try:
                recorder = PvRecorder(device_index=mic_index, frame_length=512)
                print(f"  ✓ Microphone #{mic_index} works")
                recorder.delete()
            except Exception as e:
                print(f"  ✗ Microphone #{mic_index} failed: {e}")
                print(f"     Consider removing MICROPHONE_INDEX from .env")
                return False
        
        return True
        
    except ImportError:
        print("✗ PvRecorder not installed (check Dependencies step)")
        return False
    except Exception as e:
        print(f"✗ Error checking microphone: {e}")
        return False

def check_porcupine_initialization():
    """Test actual Porcupine initialization"""
    print("\n" + "="*70)
    print("🚀 TESTING PORCUPINE INITIALIZATION")
    print("="*70)
    
    load_dotenv()
    
    try:
        import pvporcupine
        from pvrecorder import PvRecorder
        
        access_key = os.getenv("PORCUPINE_ACCESS_KEY", "").strip()
        
        # Find wake word file
        wake_words_dir = Path("wake_words")
        ppn_files = list(wake_words_dir.glob("**/*.ppn"))
        
        if not ppn_files:
            print("✗ No .ppn files found (see Wake Word Files section above)")
            return False
        
        wake_word_file = str(ppn_files[0])
        print(f"Testing with: {wake_word_file}")
        
        # Try to initialize Porcupine
        try:
            porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[wake_word_file],
                sensitivities=[0.5]
            )
            print("✓ Porcupine initialized successfully")
            
            # Try to initialize recorder
            try:
                recorder = PvRecorder(
                    frame_length=porcupine.frame_length,
                    device_index=-1
                )
                print("✓ PvRecorder initialized successfully")
                print(f"  Frame length: {porcupine.frame_length}")
                print(f"  Sample rate: {porcupine.sample_rate}")
                
                recorder.delete()
                porcupine.delete()
                return True
                
            except Exception as e:
                print(f"✗ PvRecorder failed: {e}")
                porcupine.delete()
                return False
        
        except Exception as e:
            print(f"✗ Porcupine initialization failed: {e}")
            print("\n  Possible causes:")
            print("  - Invalid access key")
            print("  - Invalid .ppn file for your OS (need Windows version)")
            print("  - .ppn file is corrupted")
            return False
    
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def main():
    """Run all diagnostics"""
    print("\n" + "="*70)
    print("🔧 PORCUPINE WAKE WORD DIAGNOSTICS")
    print("="*70)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Access Key", check_access_key),
        ("Wake Word Files", check_wake_word_file),
        ("Personality Config", check_personality_config),
        ("Microphone", check_microphone),
        ("Porcupine Initialization", check_porcupine_initialization),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nResult: {passed}/{total} checks passed\n")
    
    if passed == total:
        print("✓ Everything looks good! Try running main.py")
        print("\nTroubleshooting tips if wake words still don't work:")
        print("  1. Make sure you're speaking clearly and at normal volume")
        print("  2. Try increasing PORCUPINE_SENSITIVITY in .env (0.5 → 0.7)")
        print("  3. Check for background noise - test with python tools/test_porcupine_live.py")
        print("  4. Verify your microphone is not in use by another application")
    else:
        print("✗ Fix the failed checks above before running main.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
