#!/usr/bin/env python3
"""
R2 Simple Sound System
Simplified letter-based vocabulary for network scanner operations.

This replaces the complex emotion-phrase system with simple letter mappings
that can be easily extended.
"""

import os
import logging
import wave
from typing import Dict, List, Optional
from pathlib import Path
import threading
import time

# Audio dependencies
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available - R2 will be silent until installed")

logger = logging.getLogger(__name__)

class R2SimpleSounds:
    """
    Simplified R2 sound system using direct letter mappings.
    Easy to extend by just adding new letter combinations.
    """
    
    def __init__(self, sounds_directory: str = None, audio_device: str = None):
        """Initialize R2's simplified sound system."""
        
        # Default sounds directory
        if sounds_directory is None:
            sounds_directory = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'data', 'sounds'
            )
        
        self.sounds_dir = Path(sounds_directory)
        self.audio_device = audio_device
        self.audio_devices_to_try = [
            'default',     # System default
            'hw:3,0',      # USB Audio Card 3
            'hw:1,0',      # Analog audio card 1
            'hw:0,3',      # HDMI audio
            None           # Let pygame choose
        ]
        self.is_initialized = False
        
        # Available letter sounds
        self.available_letters = [
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            'c1', 'g1', 'o1', 's1', 'u1'  # Alternate sounds
        ]
        
        # Letter-based syllabary (preloaded audio data)
        self.syllabary = {}
        
        # =======================================
        # SIMPLE VOCABULARY - Easy to extend!
        # =======================================
        
        # Core scanner vocabulary (start with single letters)
        self.scanner_vocabulary = {
            # Basic operations
            'scan_start': 'q a',              # Single letter A for scan start
            'device_found': 'z',            # Single letter Z for device found  
            'scan_complete': 'c1',          # c1 (alternate C) for completion
            
            # Port scanning operations
            'port_scan_start': 'a s1',         # Same as scan_start - letter A
            'port_found': 'z s1',           # Z + S1 for port found (extends device_found)
            
            
            # Can easily extend further:
            'scan_error': 'c g1',          # c g1 for error
            # 'timeout': 'n o',             # N + O for timeout
            'startup': 'v y',               # v y for startup
            'shutdown': 'q q v',            # shutdown sequence
        }
        
        # Initialize audio system
        self._init_audio()
        
        # Load letter-based syllabary
        self._load_syllabary()
    
    def _init_audio(self):
        """Initialize the audio system with fallback devices."""
        if not PYGAME_AVAILABLE:
            logger.warning("🤖 R2 audio system unavailable - pygame not installed")
            return
        
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=4096)
        pygame.mixer.init()
        
        # Test audio device
        self._test_audio_device()
        
        if pygame.mixer.get_init():
            self.is_initialized = True
            logger.info(f"🔊 R2 simple audio system initialized on device: {self.audio_device or 'default'}")
        else:
            logger.warning("🔇 R2 audio system failed to initialize")
    
    def _test_audio_device(self):
        """Test the current audio device."""
        try:
            # Generate a brief test tone
            pygame.mixer.music.set_volume(0.1)  # Very quiet test
            logger.debug("🔊 R2 audio device test completed")
        except Exception as e:
            logger.warning(f"⚠️  Audio device test error: {e}")
    
    def _load_syllabary(self):
        """Load letter-based WAV files into memory."""
        logger.info("🎵 R2 loading simple syllabary...")
        
        loaded_count = 0
        for letter in self.available_letters:
            wav_path = self.sounds_dir / f"{letter}.wav"
            if wav_path.exists():
                try:
                    with wave.open(str(wav_path), "rb") as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        self.syllabary[letter] = audio_data
                    loaded_count += 1
                    logger.debug(f"  Loaded: {letter}.wav")
                except Exception as e:
                    logger.warning(f"  Failed to load {letter}.wav: {e}")
            else:
                logger.debug(f"  Missing: {letter}.wav")
        
        logger.info(f"🤖 R2 simple syllabary loaded: {loaded_count}/{len(self.available_letters)} sounds")
    
    def play_scanner_event(self, event: str, volume: float = 0.7):
        """
        Play a sound for a scanner event using our simple vocabulary.
        
        Args:
            event: Scanner event (e.g., 'scan_start', 'device_found', 'scan_complete')
            volume: Volume level (0.0 to 1.0)
        """
        if not self.is_initialized:
            logger.debug(f"🤖 R2 would play: {event}")
            return
        
        # Get letter sequence for this event
        letter_sequence = self.scanner_vocabulary.get(event)
        if not letter_sequence:
            logger.warning(f"🔇 R2 doesn't know event: {event}")
            return
        
        logger.debug(f"🤖 R2 playing '{event}' → '{letter_sequence}'")
        
        # Play the letter sequence
        self._play_letter_sequence(letter_sequence, volume)
    
    def _play_letter_sequence(self, letter_sequence: str, volume: float = 0.7):
        """Play a sequence of letters."""
        if not self.syllabary:
            logger.warning("🔇 R2 syllabary not loaded")
            return
        
        # Generate concatenated audio data
        audio_data = self._generate_audio(letter_sequence)
        
        if audio_data:
            # Play using pygame in a separate thread
            threading.Thread(
                target=self._play_raw_audio_data,
                args=(audio_data, volume),
                daemon=True
            ).start()
        else:
            logger.warning(f"🔇 R2 couldn't generate audio for: {letter_sequence}")
    
    def _generate_audio(self, letter_sequence: str) -> bytes:
        """Generate audio data by concatenating letter sounds."""
        if not self.syllabary:
            return b""
        
        audio_data = b""
        letters = letter_sequence.split() if ' ' in letter_sequence else [letter_sequence]
        
        for letter in letters:
            letter = letter.lower()
            if letter in self.syllabary:
                audio_data += self.syllabary[letter]
            else:
                logger.debug(f"🔇 R2 missing letter sound: {letter}")
        
        return audio_data
    
    def _play_raw_audio_data(self, audio_data: bytes, volume: float):
        """Play raw audio data using pygame."""
        if not PYGAME_AVAILABLE:
            return
        
        try:
            import tempfile
            
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # mono
                    wav_file.setsampwidth(2)  # 16 bits  
                    wav_file.setframerate(22050)  # 22kHz
                    wav_file.writeframes(audio_data)
                
                # Play using external player for reliability
                import subprocess
                players = [
                    ['ffplay', '-nodisp', '-autoexit', '-v', 'quiet', temp_file.name],
                    ['aplay', temp_file.name],
                    ['paplay', temp_file.name]
                ]
                
                for player_cmd in players:
                    try:
                        result = subprocess.run(player_cmd, capture_output=True, timeout=5)
                        if result.returncode == 0:
                            break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                # Clean up
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"🔇 R2 audio playback failed: {e}")
    
    def add_vocabulary(self, event: str, letter_sequence: str):
        """
        Add a new event to the vocabulary.
        
        Args:
            event: Event name (e.g., 'port_found')
            letter_sequence: Letter sequence (e.g., 'p o' or 'z')
        """
        self.scanner_vocabulary[event] = letter_sequence
        logger.info(f"🤖 R2 learned new vocabulary: '{event}' → '{letter_sequence}'")
    
    def list_vocabulary(self):
        """List current vocabulary."""
        print("🤖 R2 Current Vocabulary:")
        print("=" * 40)
        for event, letters in self.scanner_vocabulary.items():
            print(f"  {event:15} → '{letters}'")
    
    def shutdown(self):
        """Shutdown the audio system."""
        if PYGAME_AVAILABLE and pygame.mixer.get_init():
            pygame.mixer.quit()
            logger.info("🔇 R2 simple audio system shutdown")


# Global instance
r2_simple = None

def init_simple_r2_audio(sounds_directory: str = None, audio_device: str = None) -> R2SimpleSounds:
    """Initialize the global simple R2 sound engine."""
    global r2_simple
    r2_simple = R2SimpleSounds(sounds_directory, audio_device)
    return r2_simple

def play_scanner_event(event: str, volume: float = 0.7):
    """Play a scanner event using the global simple R2 sound engine."""
    global r2_simple
    if r2_simple is None:
        r2_simple = R2SimpleSounds()
    r2_simple.play_scanner_event(event, volume)

def add_r2_vocabulary(event: str, letter_sequence: str):
    """Add vocabulary to the global R2 sound engine."""
    global r2_simple
    if r2_simple is None:
        r2_simple = R2SimpleSounds()
    r2_simple.add_vocabulary(event, letter_sequence)


if __name__ == "__main__":
    # Test the simple sound system
    print("🤖 R2 Simple Sound System Test")
    
    # Initialize
    engine = init_simple_r2_audio()
    
    # Show vocabulary
    engine.list_vocabulary()
    
    # Test the three core events
    print("\n🔊 Testing core scanner sequence:")
    
    print("1. Scan starting...")
    engine.play_scanner_event('scan_start')
    time.sleep(2)
    
    print("2. Device found!")
    engine.play_scanner_event('device_found') 
    time.sleep(2)
    
    print("3. Scan complete!")
    engine.play_scanner_event('scan_complete')
    time.sleep(2)
    
    # Test adding new vocabulary
    print("\n🔧 Adding new vocabulary...")
    engine.add_vocabulary('port_found', 'p o')
    engine.add_vocabulary('scan_error', 'e r')
    
    # Test new vocabulary
    print("4. Port found!")
    engine.play_scanner_event('port_found')
    time.sleep(2)
    
    print("5. Scan error!")
    engine.play_scanner_event('scan_error')
    time.sleep(2)
    
    print("🎵 Simple sound test complete!")
    engine.shutdown()
