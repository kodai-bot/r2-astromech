"""
R2 Astromech Project - R2 Sound System
Handles R2's emotional audio expressions using WAV samples

This module maps network scanning events to R2's emotional responses,
playing appropriate sound samples to give R2 personality and feedback.
"""

import os
import logging
import random
import wave
from typing import Dict, List, Optional
from pathlib import Path
import threading
import time

# Audio dependencies (will be installed as needed)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available - R2 will be silent until installed")

logger = logging.getLogger(__name__)

class R2SoundEngine:
    """
    R2's emotional sound system.
    Maps events and emotions to authentic R2-D2 WAV samples.
    """
    
    def __init__(self, sounds_directory: str = None, audio_device: str = None):
        """
        Initialize R2's sound system.
        
        Args:
            sounds_directory: Path to directory containing R2 WAV files
            audio_device: ALSA device name (e.g., 'hw:3,0' for USB card 3)
        """
        # Default sounds directory
        if sounds_directory is None:
            sounds_directory = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'data', 'sounds'
            )
        
        self.sounds_dir = Path(sounds_directory)
        self.audio_device = audio_device
        self.audio_devices_to_try = [
            'default',     # System default (works with PipeWire/PulseAudio)
            'hw:3,0',      # USB Audio Card 3 (Traktor) - direct hardware
            'hw:1,0',      # Analog audio card 1
            'hw:0,3',      # HDMI audio
            None           # Let pygame choose
        ]
        self.is_initialized = False
        self.sound_cache = {}
        
        # Create sounds directory if it doesn't exist
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Available letter sounds (based on your WAV collection)
        self.available_letters = [
            "a", "b", "c", "c1", "d", "e", "f", "g", "g1", "h", "i", "j", "k",
            "l", "m", "n", "o", "o1", "p", "q", "r", "s", "s1", "t", "u", "u1",
            "v", "w", "x", "y", "z"
        ]
        
        # Letter-based syllabary (preloaded audio data)
        self.syllabary = {}
        
        # R2 Emotional Sound Mapping using letter combinations
        # These create R2-like phrases from letter combinations
        self.emotion_sounds = {
            # Success & Discovery
            'excited': ['woohoo', 'beepbeep', 'trillup'],  # Will map to letter sequences
            'success': ['yayaya', 'goodgood', 'wootroo'],
            'curious': ['huhwhat', 'hmmmm', 'whatwhat'],
            
            # Working & Processing  
            'working': ['beepdoop', 'whirrbuzz', 'process'],
            'thinking': ['hmmmm', 'thinkthink', 'process'],
            'acknowledging': ['beep', 'roger', 'yes'],
            
            # Alerts & Problems
            'alert': ['alert', 'beepbeep', 'urgent'],
            'warning': ['warning', 'uhoh', 'careful'],
            'error': ['error', 'nono', 'failed'],
            'frustrated': ['grumble', 'annoyed', 'frustrated'],
            
            # Social & Interactive
            'greeting': ['hello', 'hihi', 'greeting'],
            'goodbye': ['bye', 'goodbye', 'seeya'],
            'confused': ['huh', 'confused', 'whatwhat'],
            
            # NEW: More variety for scanner events
            'discovering': ['oooh', 'interesting', 'looky'],
            'analyzing': ['scanning', 'checking', 'looking'],
            'alert_positive': ['alert', 'beepbeep', 'found'],
            'quiet_working': ['working', 'processing', 'scanning'],
            'satisfaction': ['ahh', 'good', 'nice']
        }
        
        # Map emotion phrases to letter sequences
        # This is where we'll map your categorized sounds
        self.phrase_to_letters = {
            # Excitement/Success patterns
            'woohoo': 'w o o h o o',
            'beepbeep': 'b e e p b e e p',
            'trillup': 't r i l l u p',
            'yayaya': 'y a y a y a',
            'goodgood': 'g o o d g o o d',
            'wootroo': 'w o o t r o o',
            
            # Working/Processing patterns  
            'beepdoop': 'b e e p d o o p',
            'whirrbuzz': 'w h i r r b u z z',
            'process': 'p r o c e s s',
            
            # Questions/Curiosity
            'huhwhat': 'h u h w h a t',
            'hmmmm': 'h m m m m',
            'whatwhat': 'w h a t w h a t',
            'thinkthink': 't h i n k t h i n k',
            
            # Acknowledgment
            'beep': 'b e e p',
            'roger': 'r o g e r',
            'yes': 'y e s',
            
            # Alerts/Problems
            'alert': 'a l e r t',
            'urgent': 'u r g e n t',
            'warning': 'w a r n i n g',
            'uhoh': 'u h o h',
            'careful': 'c a r e f u l',
            'error': 'e r r o r',
            'nono': 'n o n o',
            'failed': 'f a i l e d',
            'grumble': 'g r u m b l e',
            'annoyed': 'a n n o y e d',
            'frustrated': 'f r u s t r a t e d',
            
            # Social
            'hello': 'h e l l o',
            'hihi': 'h i h i',
            'greeting': 'g r e e t i n g',
            'bye': 'b y e',
            'goodbye': 'g o o d b y e',
            'seeya': 's e e y a',
            'huh': 'h u h',
            'confused': 'c o n f u s e d',
            
            # NEW: Additional phrases for scanner variety
            'oooh': 'o o o h',
            'interesting': 'i n t e r e s t i n g',
            'looky': 'l o o k y',
            'scanning': 's c a n n i n g',
            'checking': 'c h e c k i n g',
            'looking': 'l o o k i n g',
            'found': 'f o u n d',
            'ahh': 'a h h',
            'good': 'g o o d',
            'nice': 'n i c e',
            'processing': 'p r o c e s s i n g'
        }
        
        # Network Event to Emotion Mapping (IMPROVED for variety)
        self.event_emotions = {
            # Basic system events (frequent, should be subtle)
            'startup': 'greeting',
            'shutdown': 'goodbye',
            'scan_start': 'quiet_working',        # More subtle than 'working'
            'scan_progress': 'quiet_working',     # Quiet ongoing work
            'idle': 'acknowledging',
            
            # Discovery events (different types get different emotions)
            'device_found': 'discovering',        # NEW: special for device discovery
            'port_found': 'alert_positive',       # NEW: positive alert for ports
            'protocol_detected': 'excited',       # Keep excited for protocols (rare)
            
            # Analysis events (thinking/investigating)
            'port_scan_start': 'analyzing',       # NEW: specific for analysis start
            'port_scan_complete': 'satisfaction', # NEW: quiet completion
            'analyzing_device': 'thinking',       # Deep thinking sounds
            'iot_scan_start': 'curious',          # Curious about IoT devices
            
            # Completion events
            'scan_complete': 'success',           # Major completion - celebrate
            
            # Error events (each gets unique emotion for variety)
            'scan_error': 'error',               # General errors
            'scan_interrupted': 'confused',      # Confusion when interrupted
            'timeout_error': 'frustrated',       # Frustration with timeouts
            'connection_failed': 'warning'       # Warning for connection issues
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
        
        # If specific device requested, try only that
        if self.audio_device:
            devices_to_try = [self.audio_device]
        else:
            devices_to_try = self.audio_devices_to_try
        
        for device in devices_to_try:
            try:
                logger.debug(f"🔊 R2 trying audio device: {device}")
                
                # Set up environment for this device
                if device and device != 'default':
                    os.environ['SDL_AUDIODRIVER'] = 'alsa'
                    os.environ['ALSA_PCM_DEVICE'] = device
                elif device == 'default':
                    os.environ.pop('SDL_AUDIODRIVER', None)
                    os.environ.pop('ALSA_PCM_DEVICE', None)
                else:
                    # Let pygame choose
                    os.environ.pop('SDL_AUDIODRIVER', None)
                    os.environ.pop('ALSA_PCM_DEVICE', None)
                
                pygame.mixer.pre_init(
                    frequency=22050,    # Match your WAV files
                    size=-16,          # 16-bit signed
                    channels=1,        # Mono (your WAV files are mono)
                    buffer=1024        # Larger buffer for stability
                )
                pygame.mixer.init()
                
                # Test if it actually worked
                test_info = pygame.mixer.get_init()
                if test_info:
                    self.is_initialized = True
                    self.audio_device = device  # Remember which device worked
                    logger.info(f"🔊 R2 audio system initialized on device: {device or 'auto'}")
                    
                    # Scan for available sound files
                    self._scan_sound_files()
                    return
                else:
                    pygame.mixer.quit()
                    
            except Exception as e:
                logger.debug(f"   Device {device} failed: {e}")
                try:
                    pygame.mixer.quit()
                except:
                    pass
                continue
        
        # If we get here, no device worked
        logger.error("🔇 R2 audio system failed to initialize on any device")
        logger.error("   Available devices: USB (hw:3,0), Analog (hw:1,0), HDMI (hw:0,3)")
        self.is_initialized = False
    
    def _test_audio_device(self):
        """Test if the audio device is working."""
        try:
            # Quick test of audio system
            test_info = pygame.mixer.get_init()
            if test_info:
                freq, fmt, channels = test_info
                logger.info(f"🎵 Audio device ready: {freq}Hz, {channels} channels")
            else:
                logger.warning("⚠️  Audio device test failed")
        except Exception as e:
            logger.warning(f"⚠️  Audio device test error: {e}")
    
    def _scan_sound_files(self):
        """Scan the sounds directory for available WAV files."""
        if not self.sounds_dir.exists():
            logger.warning(f"🔇 R2 sounds directory not found: {self.sounds_dir}")
            return
            
        wav_files = list(self.sounds_dir.glob("*.wav"))
        logger.info(f"🎵 R2 found {len(wav_files)} sound files")
        
        if len(wav_files) == 0:
            logger.warning("🔇 No WAV files found - R2 will be silent")
            logger.info(f"   Place R2 sound files in: {self.sounds_dir}")
    
    def _load_syllabary(self):
        """Load letter-based WAV files into memory for quick access."""
        logger.info("🎵 R2 loading syllabary...")
        
        for letter in self.available_letters:
            wav_path = self.sounds_dir / f"{letter}.wav"
            if wav_path.exists():
                try:
                    # Load WAV data into memory
                    with wave.open(str(wav_path), "rb") as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        self.syllabary[letter] = audio_data
                    logger.debug(f"  Loaded: {letter}.wav")
                except Exception as e:
                    logger.warning(f"  Failed to load {letter}.wav: {e}")
            else:
                logger.debug(f"  Missing: {letter}.wav")
        
        logger.info(f"🤖 R2 syllabary loaded: {len(self.syllabary)}/{len(self.available_letters)} sounds")
    
    def _generate_phrase_audio(self, phrase: str) -> bytes:
        """
        Generate audio data by concatenating letter sounds.
        Based on the TTAstromech approach.
        
        Args:
            phrase: Space-separated letter sequence (e.g., 'b e e p')
            
        Returns:
            Concatenated audio data
        """
        if not self.syllabary:
            logger.warning("🔇 R2 syllabary not loaded")
            return b""
        
        audio_data = b""
        letters = phrase.split()
        previous_letter = ""
        
        # Handle double letters (use c1, g1, etc. for repeated letters)
        double_letters = [letter[0] for letter in self.available_letters if '1' in letter]
        
        for letter in letters:
            letter = letter.lower()
            if letter in self.syllabary:
                # Use alternate sound for repeated letters if available
                if letter == previous_letter and letter in double_letters:
                    alt_letter = letter + "1"
                    if alt_letter in self.syllabary:
                        audio_data += self.syllabary[alt_letter]
                    else:
                        audio_data += self.syllabary[letter]
                else:
                    audio_data += self.syllabary[letter]
                previous_letter = letter
            else:
                logger.debug(f"🔇 R2 missing letter sound: {letter}")
        
        return audio_data
    
    def play_emotion(self, emotion: str, volume: float = 0.7):
        """
        Play a sound representing the given emotion using letter combinations.
        
        Args:
            emotion: The emotion to express (e.g., 'excited', 'error')
            volume: Volume level (0.0 to 1.0)
        """
        if not self.is_initialized:
            logger.debug(f"🤖 R2 would express: {emotion}")
            return
            
        # Get sound options for this emotion
        sound_phrases = self.emotion_sounds.get(emotion, ['beep'])
        
        # Pick a random phrase for variety
        chosen_phrase = random.choice(sound_phrases)
        
        # Convert phrase to letter sequence
        letter_sequence = self.phrase_to_letters.get(chosen_phrase, 'b e e p')  # Default fallback
        
        logger.debug(f"🤖 R2 expressing '{emotion}' with phrase '{chosen_phrase}' → '{letter_sequence}'")
        
        # Generate and play the audio
        self._play_letter_sequence(letter_sequence, volume)
    
    def _play_letter_sequence(self, letter_sequence: str, volume: float = 0.7):
        """
        Play a sequence of letters as concatenated audio.
        
        Args:
            letter_sequence: Space-separated letters (e.g., 'b e e p')
            volume: Volume level (0.0 to 1.0)
        """
        if not self.syllabary:
            logger.warning("🔇 R2 syllabary not loaded - cannot play letter sequence")
            return
        
        # Generate concatenated audio data
        audio_data = self._generate_phrase_audio(letter_sequence)
        
        if audio_data:
            # Play using pygame in a separate thread
            threading.Thread(
                target=self._play_raw_audio_data,
                args=(audio_data, volume),
                daemon=True
            ).start()
        else:
            logger.warning(f"🔇 R2 couldn't generate audio for: {letter_sequence}")
    
    def _play_raw_audio_data(self, audio_data: bytes, volume: float):
        """
        Play raw audio data using pygame.
        Based on TTAstromech approach but using pygame.
        """
        if not PYGAME_AVAILABLE:
            logger.warning("🔇 R2 cannot play audio - pygame not available")
            return
            
        try:
            import tempfile
            
            # Create a temporary WAV file with the concatenated data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Write WAV header and data
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # mono
                    wav_file.setsampwidth(2)  # 16 bits  
                    wav_file.setframerate(22050)  # 22kHz
                    wav_file.writeframes(audio_data)
                
                logger.debug(f"🔊 R2 playing audio file: {temp_file.name}")
                logger.debug(f"🔊 Audio data size: {len(audio_data)} bytes")
                
                # Also save to data/sounds for debugging
                debug_file = os.path.join(self.sounds_dir, 'last_r2_output.wav')
                import shutil
                shutil.copy2(temp_file.name, debug_file)
                logger.debug(f"🔊 Saved debug copy to: {debug_file}")
                
                # Skip pygame and use external player directly for reliable audio
                # pygame is routing to wrong/silent device in this environment
                logger.debug("🔊 R2 using external audio player for reliable playback...")
                
                import subprocess
                players = [
                    ['ffplay', '-nodisp', '-autoexit', '-v', 'quiet', temp_file.name],
                    ['aplay', temp_file.name],
                    ['paplay', temp_file.name]
                ]
                
                playback_success = False
                for player_cmd in players:
                    try:
                        result = subprocess.run(player_cmd, capture_output=True, timeout=10)
                        if result.returncode == 0:
                            logger.debug(f"🔊 R2 external player {player_cmd[0]} succeeded")
                            playback_success = True
                            break
                        else:
                            logger.debug(f"🔇 R2 {player_cmd[0]} failed: {result.stderr.decode()}")
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        logger.debug(f"🔇 R2 {player_cmd[0]} not available")
                        continue
                
                if not playback_success:
                    logger.warning("🔇 R2 all external audio players failed, trying pygame fallback...")
                    try:
                        # Fallback to pygame if external players fail
                        sound = pygame.mixer.Sound(temp_file.name)
                        sound.set_volume(volume)
                        channel = sound.play()
                        
                        logger.debug(f"🔊 R2 fallback pygame playback, volume: {volume}")
                        
                        # Wait for sound to finish
                        start_time = time.time()
                        while pygame.mixer.get_busy():
                            time.sleep(0.1)
                            if time.time() - start_time > 10:
                                logger.warning("🔇 R2 pygame fallback timeout")
                                break
                        
                        duration = time.time() - start_time
                        logger.debug(f"🔊 R2 pygame fallback finished, duration: {duration:.2f}s")
                        
                    except Exception as pygame_error:
                        logger.error(f"🔇 R2 pygame fallback also failed: {pygame_error}")
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
        except Exception as e:
            logger.error(f"🔇 R2 audio playback error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def play_event(self, event: str, volume: float = 0.7):
        """
        Play sound for a specific network scanning event.
        
        Args:
            event: The event type (e.g., 'device_found', 'scan_complete')
            volume: Volume level (0.0 to 1.0)
        """
        # Map event to emotion
        emotion = self.event_emotions.get(event, 'acknowledging')
        
        logger.debug(f"🤖 R2 event '{event}' → emotion '{emotion}'")
        self.play_emotion(emotion, volume)
    
    def speak_phrase(self, phrase: str, volume: float = 0.7):
        """
        Make R2 speak a custom phrase using letter sounds.
        
        Args:
            phrase: Text phrase to convert to R2 speech
            volume: Volume level (0.0 to 1.0)
        """
        # Convert text to simple letter sequence
        letter_sequence = ' '.join(phrase.lower().replace(' ', ''))
        logger.info(f"🤖 R2 speaking: '{phrase}' → '{letter_sequence}'")
        self._play_letter_sequence(letter_sequence, volume)
    
    def add_emotion_phrase(self, emotion: str, phrase_name: str, letter_sequence: str):
        """
        Add a custom emotion phrase mapping.
        
        Args:
            emotion: Emotion name (e.g., 'excited')
            phrase_name: Name of the phrase (e.g., 'woohoo')
            letter_sequence: Space-separated letters (e.g., 'w o o h o o')
        """
        # Add to phrase mapping
        self.phrase_to_letters[phrase_name] = letter_sequence
        
        # Add to emotion if not exists
        if emotion not in self.emotion_sounds:
            self.emotion_sounds[emotion] = []
        
        # Add phrase to emotion options
        if phrase_name not in self.emotion_sounds[emotion]:
            self.emotion_sounds[emotion].append(phrase_name)
        
        logger.info(f"🤖 R2 learned: {emotion} → '{phrase_name}' ({letter_sequence})")
    
    def test_audio_system(self):
        """Test the audio system with a simple beep."""
        logger.info("🧪 R2 testing audio system...")
        self.play_emotion('greeting')
        time.sleep(1)
        self.play_emotion('success') 
        logger.info("🔊 R2 audio test complete")
    
    def list_available_sounds(self) -> List[str]:
        """List all available sound files."""
        if not self.sounds_dir.exists():
            return []
        
        wav_files = [f.stem for f in self.sounds_dir.glob("*.wav")]
        return sorted(wav_files)
    
    def add_custom_emotion_mapping(self, emotion: str, sound_files: List[str]):
        """
        Add custom emotion to sound file mapping.
        
        Args:
            emotion: Name of the emotion
            sound_files: List of sound file names (without .wav extension)
        """
        self.emotion_sounds[emotion] = sound_files
        logger.info(f"🤖 R2 learned new emotion: {emotion}")
    
    def shutdown(self):
        """Shutdown the audio system gracefully."""
        if self.is_initialized:
            self.play_emotion('goodbye')
            time.sleep(1)  # Let goodbye sound finish
            pygame.mixer.quit()
            logger.info("🔇 R2 audio system shutdown")


# Global R2 sound engine instance
r2_sound = None

def init_r2_audio(sounds_directory: str = None, audio_device: str = None) -> R2SoundEngine:
    """
    Initialize the global R2 sound engine.
    
    Args:
        sounds_directory: Path to R2 sound files
        audio_device: ALSA device (e.g., 'hw:3,0' for USB card 3)
        
    Returns:
        R2SoundEngine instance
    """
    global r2_sound
    r2_sound = R2SoundEngine(sounds_directory, audio_device)
    return r2_sound

def list_audio_devices():
    """List available audio devices for configuration."""
    print("🔊 Available Audio Devices:")
    print("=" * 40)
    
    try:
        # List ALSA devices
        import subprocess
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Could not list audio devices")
            
        print("\n💡 For R2 audio:")
        print("   USB Audio Card 3: audio_device='hw:3,0'")
        print("   Default device: audio_device=None")
        
    except Exception as e:
        print(f"Error listing devices: {e}")

def test_usb_audio():
    """Quick test of USB audio device."""
    print("🧪 Testing USB Audio Device...")
    
    try:
        # Test with aplay
        import subprocess
        import tempfile
        import wave
        import numpy as np
        
        # Generate a test tone
        sample_rate = 22050
        duration = 1.0
        frequency = 440  # A note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        tone = np.sin(2 * np.pi * frequency * t) * 0.3
        tone_16bit = (tone * 32767).astype(np.int16)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(tone_16bit.tobytes())
            
            # Test playback on USB audio device
            print("  🔊 Testing USB audio card (hw:3,0)...")
            result = subprocess.run(['aplay', '-D', 'hw:3,0', temp_file.name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✅ USB audio device working!")
            else:
                print(f"  ❌ USB audio test failed: {result.stderr}")
            
            os.unlink(temp_file.name)
            
    except ImportError:
        print("  ⚠️  numpy not available - using basic test")
        print("  Run: pip install numpy")
    except Exception as e:
        print(f"  ❌ Test failed: {e}")

def test_r2_audio_file():
    """Test R2 audio by playing the last generated file with external player."""
    print("🧪 Testing R2 Generated Audio File...")
    
    import subprocess
    audio_file = "data/sounds/last_r2_output.wav"
    
    if not os.path.exists(audio_file):
        print(f"  ❌ No R2 audio file found at {audio_file}")
        print("     Run a test that generates audio first (e.g., option 6)")
        return
    
    print(f"  📁 Found R2 audio file: {audio_file}")
    
    # Try different audio players
    players = [
        (['aplay', audio_file], "aplay (ALSA)"),
        (['paplay', audio_file], "paplay (PulseAudio)"),
        (['ffplay', '-nodisp', '-autoexit', audio_file], "ffplay"),
        (['mplayer', audio_file], "mplayer")
    ]
    
    for command, player_name in players:
        try:
            print(f"  🔊 Testing with {player_name}...")
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ {player_name} played successfully!")
                print("     Did you hear R2 say 'hello'?")
                return
            else:
                print(f"  ❌ {player_name} failed: {result.stderr.strip()}")
        except FileNotFoundError:
            print(f"  ⚠️  {player_name} not installed")
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  {player_name} timeout")
        except Exception as e:
            print(f"  ❌ {player_name} error: {e}")
    
    print("  💡 If no player worked, try manually:")
    print(f"     aplay {audio_file}")
    print(f"     Or copy {audio_file} to another machine to test")

def play_r2_event(event: str, volume: float = 0.7):
    """
    Convenience function to play R2 sound for an event.
    
    Args:
        event: Event name (e.g., 'device_found')
        volume: Volume level (0.0 to 1.0)
    """
    global r2_sound
    if r2_sound is None:
        r2_sound = R2SoundEngine()
    
    r2_sound.play_event(event, volume)

def play_r2_emotion(emotion: str, volume: float = 0.7):
    """
    Convenience function to play R2 sound for an emotion.
    
    Args:
        emotion: Emotion name (e.g., 'excited')
        volume: Volume level (0.0 to 1.0)  
    """
    global r2_sound
    if r2_sound is None:
        r2_sound = R2SoundEngine()
    
    r2_sound.play_emotion(emotion, volume)


if __name__ == "__main__":
    # Test the sound system
    print("🤖 R2 Sound System Test")
    
    # Initialize audio
    engine = init_r2_audio()
    
    # Test basic emotions
    print("Testing emotions...")
    emotions = ['greeting', 'working', 'excited', 'success', 'error', 'goodbye']
    
    for emotion in emotions:
        print(f"  🔊 Testing {emotion}...")
        engine.play_emotion(emotion)
        time.sleep(1.5)
    
    # Test events
    print("Testing network events...")
    events = ['scan_start', 'device_found', 'port_found', 'scan_complete']
    
    for event in events:
        print(f"  📡 Testing {event}...")
        engine.play_event(event)
        time.sleep(1.5)
    
    print("🎵 R2 sound test complete!")
    engine.shutdown()
