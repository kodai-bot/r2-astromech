#!/usr/bin/env python3
"""
R2 Sound System Test & Categorization Helper

This script helps you:
1. Test individual letter sounds
2. Test emotion phrases
3. Categorize sounds by listening and assigning emotions
4. Test network scanner integration
"""

import sys
import os
import time

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personality.r2_sounds import R2SoundEngine, init_r2_audio, play_r2_emotion, list_audio_devices, test_usb_audio, test_r2_audio_file
from personality.r2_simple_sounds import R2SimpleSounds, play_scanner_event, init_simple_r2_audio

def test_individual_letters():
    """Test individual letter sounds to understand what we have."""
    print("\n🎵 Testing Individual Letter Sounds")
    print("=" * 50)
    
    # Initialize with automatic device fallback
    engine = R2SoundEngine()
    
    if not engine.syllabary:
        print("❌ No syllabary loaded. Check that WAV files are in data/sounds/")
        return
    
    if not engine.is_initialized:
        print("❌ Audio system not initialized. No sound will play.")
        return
    
    print(f"Available letters: {len(engine.syllabary)}")
    print("Letters loaded:", ', '.join(sorted(engine.syllabary.keys())))
    print(f"Audio device: {engine.audio_device}")
    
    for letter in sorted(engine.syllabary.keys()):
        print(f"  🔊 Playing: {letter}")
        engine._play_letter_sequence(letter)
        time.sleep(1.5)  # Pause between sounds

def test_emotion_phrases():
    """Test the current emotion to phrase mappings."""
    print("\n🤖 Testing Emotion Phrases")
    print("=" * 50)
    
    engine = R2SoundEngine()
    
    if not engine.is_initialized:
        print("❌ Audio system not initialized. No sound will play.")
        return
    
    print(f"Audio device: {engine.audio_device}")
    emotions_to_test = ['greeting', 'excited', 'working', 'success', 'error', 'goodbye']
    
    for emotion in emotions_to_test:
        print(f"  🎭 Testing emotion: {emotion}")
        engine.play_emotion(emotion)
        time.sleep(2)  # Pause between emotions

def test_custom_phrases():
    """Test some custom R2-like phrases."""
    print("\n🗣️  Testing Custom Phrases")
    print("=" * 50)
    
    engine = R2SoundEngine()
    
    if not engine.is_initialized:
        print("❌ Audio system not initialized. No sound will play.")
        return
    
    print(f"Audio device: {engine.audio_device}")
    test_phrases = [
        "beep",
        "woohoo", 
        "hello",
        "error",
        "scan complete"
    ]
    
    for phrase in test_phrases:
        print(f"  💬 R2 saying: '{phrase}'")
        engine.speak_phrase(phrase)
        time.sleep(2)

def test_network_scanner_events():
    """Test the OLD complex network scanner event integration."""
    print("\n📡 Testing OLD Complex Network Scanner Events") 
    print("=" * 50)
    print("NOTE: This uses the old complex emotion system")
    
    # Initialize with automatic device fallback
    engine = R2SoundEngine()
    
    if not engine.is_initialized:
        print("❌ Audio system not initialized. No sound will play.")
        return
    
    # Test various scanner events using the old system
    events = [
        'startup',
        'scan_start', 
        'device_found',
        'port_found',
        'scan_complete',
        'scan_error'
    ]
    
    for event in events:
        print(f"  🔍 Network event: {event}")
        # Use the engine's play_event method instead of play_r2_emotion
        engine.play_event(event)
        time.sleep(2)

def test_simple_scanner_events():
    """Test the NEW simplified scanner event sounds."""
    print("\n🔊 Testing NEW Simple Scanner Events") 
    print("=" * 50)
    print("This uses our new simplified letter-based vocabulary")
    
    # Initialize simple sound engine
    simple_engine = R2SimpleSounds()
    
    if not simple_engine.is_initialized:
        print("❌ Simple audio system not initialized. No sound will play.")
        return
    
    print(f"Audio device: {simple_engine.audio_device or 'default'}")
    print()
    
    # Show current vocabulary
    simple_engine.list_vocabulary()
    print()
    
    # Test scanner sequence
    scanner_events = [
        ('startup', 'v y', '🔋 R2 startup'),
        ('scan_start', 'a', '🔍 Starting scan'),
        ('device_found', 'z', '🎯 Found device'),
        ('port_scan_start', 'a', '🔬 Starting port scan'),
        ('port_found', 'z s1', '📡 Found open port'),
        ('scan_complete', 'c1', '✅ Scan complete'),
        ('scan_error', 'c g1', '❌ Scan error'),
    ]
    
    print("🤖 Testing Scanner Event Sequence:")
    print("-" * 40)
    
    for event, letters, description in scanner_events:
        print(f"  {description}")
        print(f"    Event: {event} → Letters: '{letters}'")
        simple_engine.play_scanner_event(event)
        time.sleep(3.0)  # Longer pause to hear differences
        print()
    
    print("🎵 Simple scanner test complete!")

def interactive_categorization():
    """Interactive tool to help categorize sounds by emotion."""
    print("\n🎯 Interactive Sound Categorization")
    print("=" * 50)
    print("This will help you assign emotions to letter combinations")
    print("Listen to combinations and tell me what emotion they represent")
    
    engine = R2SoundEngine()
    
    # Some test combinations to categorize
    test_combinations = [
        "b e e p",
        "w o o h o o", 
        "e r r o r",
        "a l e r t",
        "g o o d",
        "n o n o",
        "h u h",
        "y e s"
    ]
    
    categorized = {}
    
    for combo in test_combinations:
        print(f"\n  🔊 Playing: '{combo}'")
        engine._play_letter_sequence(combo)
        
        emotion = input(f"    What emotion does this represent? (excited/error/working/etc.): ").strip().lower()
        if emotion:
            categorized[combo] = emotion
            print(f"    ✅ Categorized '{combo}' as '{emotion}'")
    
    print("\n📋 Categorization Results:")
    for combo, emotion in categorized.items():
        print(f"  '{combo}' → {emotion}")

def main():
    """Main test menu."""
    print("🤖 R2-D2 Sound System Test & Categorization Tool")
    print("=" * 60)
    
    while True:
        print("\nChoose a test:")
        print("1. Test individual letter sounds")
        print("2. Test emotion phrases") 
        print("3. Test custom phrases")
        print("4. Test OLD network scanner events (complex)")
        print("5. Test NEW simple scanner events (recommended)")
        print("6. Interactive categorization helper")
        print("7. Quick sound test")
        print("8. List audio devices")
        print("9. Test USB audio device")
        print("10. Test R2 audio file playback")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-10): ").strip()
        
        try:
            if choice == '1':
                test_individual_letters()
            elif choice == '2':
                test_emotion_phrases()
            elif choice == '3':
                test_custom_phrases()
            elif choice == '4':
                test_network_scanner_events()
            elif choice == '5':
                test_simple_scanner_events()
            elif choice == '6':
                interactive_categorization()
            elif choice == '7':
                print("🔊 Quick test...")
                # Initialize with automatic device fallback
                init_r2_audio()
                play_r2_emotion('greeting')
                time.sleep(1)
                play_r2_emotion('excited')
                time.sleep(1)
                play_r2_emotion('goodbye')
            elif choice == '8':
                list_audio_devices()
            elif choice == '9':
                test_usb_audio()
            elif choice == '10':
                test_r2_audio_file()
            elif choice == '0':
                print("🤖 R2 says goodbye!")
                # Initialize with automatic device fallback
                init_r2_audio()
                play_r2_emotion('goodbye')
                time.sleep(1)
                break
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n\n🛑 Test interrupted")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
