"""
Modular Audio Engine Implementation

This module implements the IAudioEngine interface for the new modular R2 system.
It provides event-driven audio playback with proper encapsulation.
"""

import asyncio
import os
import wave
import tempfile
from typing import List, Dict, Any
from datetime import datetime

from ...core.interfaces import ModuleStatus
from ...core.events import EventBus, create_event, R2Events
from ..personality.interfaces import IAudioEngine
from ...utils.exceptions import R2ModuleException
from ...utils.logging import get_module_logger

logger = get_module_logger("personality.audio_engine")


class ModularAudioEngine(IAudioEngine):
    """
    Modular Audio Engine implementation
    
    This audio engine uses event-driven communication and follows the new
    modular architecture principles.
    """
    
    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        """
        Initialize the modular audio engine.
        
        Args:
            event_bus: Event bus for communication
            config: Audio configuration
        """
        self.event_bus = event_bus
        self.config = config
        self.logger = logger
        
        # Audio state
        self.is_running = False
        self.is_initialized = False
        self.current_volume = config.get('volume', 0.7)
        
        # Configuration
        self.audio_device = config.get('audio_device', 'default')
        self.sound_directory = config.get('sound_directory', 'data/sounds')
        self.sample_rate = config.get('sample_rate', 22050)
        self.channels = config.get('channels', 1)
        self.buffer_size = config.get('buffer_size', 4096)
        
        # Available sounds
        self.available_letters = [
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            'c1', 'g1', 'o1', 's1', 'u1'
        ]
        
        # Letter-based syllabary (preloaded audio data)
        self.syllabary = {}
        
        # Scanner vocabulary mapping
        self.scanner_vocabulary = {
            'scan_start': 'q a',           # Network scan starting
            'device_found': 'z',           # Device discovered
            'scan_complete': 'c1',         # Scan completed successfully
            'port_scan_start': 'a s1',     # Port scan starting
            'port_found': 'z s1',          # Open port found
            'scan_error': 'c g1',          # Scan error occurred
            'startup': 'v y',              # System startup
            'shutdown': 'v q q',           # System shutdown
            'progress': 'a',               # Progress indicator (short beep)
            'analyzing': 's1 o',           # Device analysis in progress
            'success': 'c c1',             # Operation successful
            # New phase-specific sounds
            'phase_start': 'o',            # Phase transition sound
            'discovery_phase': 'q a',      # Device discovery phase
            'scanning_phase': 'a s1',      # Device scanning phase
            'ssdp_discovery': 'z o',       # SSDP/UPnP discovery
            'arp_discovery': 'z',          # ARP discovery
            'mdns_discovery': 'z s1',      # mDNS discovery
        }
        
        # Statistics
        self.stats = {
            'sounds_played': 0,
            'sequences_played': 0,
            'errors': 0
        }
        
        self.logger.info("Modular Audio Engine initialized")
    
    @property
    def module_name(self) -> str:
        """Get module name"""
        return "personality.audio_engine"
    
    async def initialize(self) -> bool:
        """Initialize the audio engine module"""
        try:
            self.logger.info("Initializing audio engine...")
            
            # Load letter-based syllabary
            await self._load_syllabary()
            
            # Subscribe to relevant events
            await self.event_bus.subscribe(R2Events.NETWORK_SCAN_STARTED, self._on_scan_started)
            await self.event_bus.subscribe(R2Events.DEVICE_DISCOVERED, self._on_device_discovered)
            await self.event_bus.subscribe(R2Events.NETWORK_SCAN_COMPLETED, self._on_scan_completed)
            await self.event_bus.subscribe(R2Events.NETWORK_SCAN_ERROR, self._on_scan_error)
            await self.event_bus.subscribe(R2Events.DEVICE_ANALYZED, self._on_device_analyzed)
            await self.event_bus.subscribe(R2Events.SYSTEM_STARTUP, self._on_system_startup)
            await self.event_bus.subscribe(R2Events.SYSTEM_SHUTDOWN, self._on_system_shutdown)
            
            self.is_initialized = True
            self.logger.info("Audio engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize audio engine", error=str(e))
            raise R2ModuleException(self.module_name, f"Initialization failed: {e}", e)
    
    async def start(self) -> bool:
        """Start the audio engine module"""
        try:
            self.logger.info("Starting audio engine...")
            self.is_running = True
            
            # Play startup sound
            await self.play_sound('startup')
            
            # Publish module started event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STARTED,
                {"module": self.module_name, "capabilities": ["audio_playback", "sound_generation"]},
                self.module_name
            ))
            
            self.logger.info("Audio engine started successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to start audio engine", error=str(e))
            raise R2ModuleException(self.module_name, f"Start failed: {e}", e)
    
    async def stop(self) -> bool:
        """Stop the audio engine module"""
        try:
            self.logger.info("Stopping audio engine...")
            
            # Play shutdown sound
            await self.play_sound('shutdown')
            
            self.is_running = False
            
            # Publish module stopped event
            await self.event_bus.publish(create_event(
                R2Events.MODULE_STOPPED,
                {"module": self.module_name, "stats": self.stats},
                self.module_name
            ))
            
            self.logger.info("Audio engine stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to stop audio engine", error=str(e))
            return False
    
    async def get_status(self) -> ModuleStatus:
        """Get module status"""
        return ModuleStatus(
            name=self.module_name,
            status='running' if self.is_running else 'stopped',
            health_score=1.0 if self.is_running and self.is_initialized else 0.5,
            last_heartbeat=datetime.now(),
            uptime_seconds=0.0,  # TODO: Calculate actual uptime
            memory_usage_mb=None  # TODO: Add memory monitoring
        )
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            # Basic health check - can we access sound files?
            test_file = os.path.join(self.sound_directory, 'a.wav')
            if os.path.exists(test_file):
                return True
            else:
                self.logger.warning("Sound files not found - running in silent mode")
                return True  # Still healthy, just silent
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup module resources"""
        try:
            self.logger.info("Cleaning up audio engine...")
            
            # Clear syllabary
            self.syllabary.clear()
            
            self.logger.info("Audio engine cleanup complete")
            return True
            
        except Exception as e:
            self.logger.error("Cleanup failed", error=str(e))
            return False
    
    async def play_sound(self, sound_id: str, volume: float = 0.7) -> bool:
        """
        Play a sound by ID.
        
        Args:
            sound_id: Sound identifier
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if sound played successfully
        """
        try:
            if not self.is_running:
                self.logger.warning("Audio engine not running - sound not played")
                return False
            
            # Get letter sequence for this sound
            letter_sequence = self.scanner_vocabulary.get(sound_id)
            if not letter_sequence:
                self.logger.warning(f"Unknown sound ID: {sound_id}")
                return False
            
            self.logger.info(f"Playing sound: {sound_id} -> {letter_sequence}")
            
            # Play the letter sequence
            success = await self.play_letter_sequence(letter_sequence, volume)
            
            if success:
                self.stats['sounds_played'] += 1
                
                # Publish audio played event
                await self.event_bus.publish(create_event(
                    R2Events.AUDIO_PLAYED,
                    {
                        "sound_id": sound_id,
                        "letter_sequence": letter_sequence,
                        "volume": volume
                    },
                    self.module_name
                ))
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to play sound {sound_id}", error=str(e))
            self.stats['errors'] += 1
            return False
    
    async def play_sequence(self, sequence: List[str], volume: float = 0.7) -> bool:
        """
        Play a sequence of sounds.
        
        Args:
            sequence: List of sound IDs
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if sequence played successfully
        """
        try:
            self.logger.info(f"Playing sound sequence: {sequence}")
            
            for sound_id in sequence:
                if not await self.play_sound(sound_id, volume):
                    return False
                await asyncio.sleep(0.1)  # Small delay between sounds
            
            self.stats['sequences_played'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to play sequence {sequence}", error=str(e))
            self.stats['errors'] += 1
            return False
    
    async def play_letter_sequence(self, letters: str, volume: float = 0.7) -> bool:
        """
        Play a sequence of letter sounds.
        
        Args:
            letters: Space-separated letter sequence (e.g., "a b c")
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if sequence played successfully
        """
        try:
            if not self.syllabary:
                self.logger.warning("Syllabary not loaded - running in silent mode")
                return True  # Consider this success in silent mode
            
            # Generate concatenated audio data
            audio_data = await self._generate_audio(letters)
            
            if audio_data:
                # Play using external player for reliability
                await self._play_raw_audio_data(audio_data, volume)
                return True
            else:
                self.logger.warning(f"Couldn't generate audio for: {letters}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to play letter sequence {letters}", error=str(e))
            self.stats['errors'] += 1
            return False
    
    async def stop_audio(self) -> bool:
        """
        Stop all audio playback.
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            # For now, we can't easily stop external audio players
            # This would require more sophisticated audio management
            self.logger.info("Audio stop requested (not implemented)")
            return True
            
        except Exception as e:
            self.logger.error("Failed to stop audio", error=str(e))
            return False
    
    async def get_available_sounds(self) -> List[str]:
        """
        Get list of available sound IDs.
        
        Returns:
            List[str]: Available sound IDs
        """
        return list(self.scanner_vocabulary.keys())
    
    async def get_available_letters(self) -> List[str]:
        """
        Get list of available letter sounds.
        
        Returns:
            List[str]: Available letter sounds
        """
        return self.available_letters.copy()
    
    async def set_volume(self, volume: float) -> bool:
        """
        Set global volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if volume set successfully
        """
        try:
            self.current_volume = max(0.0, min(1.0, volume))
            self.logger.info(f"Volume set to: {self.current_volume}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set volume to {volume}", error=str(e))
            return False
    
    async def get_volume(self) -> float:
        """
        Get current volume level.
        
        Returns:
            float: Current volume level
        """
        return self.current_volume
    
    async def _load_syllabary(self) -> None:
        """Load letter-based WAV files into memory"""
        self.logger.info("Loading audio syllabary...")
        
        loaded_count = 0
        for letter in self.available_letters:
            wav_path = os.path.join(self.sound_directory, f"{letter}.wav")
            if os.path.exists(wav_path):
                try:
                    with wave.open(wav_path, "rb") as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        self.syllabary[letter] = audio_data
                    loaded_count += 1
                    self.logger.debug(f"Loaded: {letter}.wav")
                except Exception as e:
                    self.logger.warning(f"Failed to load {letter}.wav: {e}")
            else:
                self.logger.debug(f"Missing: {letter}.wav")
        
        self.logger.info(f"Audio syllabary loaded: {loaded_count}/{len(self.available_letters)} sounds")
    
    async def _generate_audio(self, letter_sequence: str) -> bytes:
        """Generate audio data by concatenating letter sounds"""
        if not self.syllabary:
            return b""
        
        audio_data = b""
        letters = letter_sequence.split() if ' ' in letter_sequence else [letter_sequence]
        
        for letter in letters:
            letter = letter.lower()
            if letter in self.syllabary:
                audio_data += self.syllabary[letter]
            else:
                self.logger.debug(f"Missing letter sound: {letter}")
        
        return audio_data
    
    async def _play_raw_audio_data(self, audio_data: bytes, volume: float) -> None:
        """Play raw audio data using external player"""
        try:
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(2)  # 16 bits
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_data)
                
                # Play using external player for reliability
                players = [
                    ['ffplay', '-nodisp', '-autoexit', '-v', 'quiet', temp_file.name],
                    ['aplay', temp_file.name],
                    ['paplay', temp_file.name]
                ]
                
                for player_cmd in players:
                    try:
                        result = await asyncio.create_subprocess_exec(
                            *player_cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await asyncio.wait_for(result.wait(), timeout=5)
                        if result.returncode == 0:
                            break
                    except (FileNotFoundError, asyncio.TimeoutError):
                        continue
                
                # Clean up
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Audio playback failed: {e}")
    
    # Event handlers
    async def _on_scan_started(self, event) -> None:
        """Handle network scan started event"""
        await self.play_sound('scan_start')
        # Log scan start details
        data = event.data
        scan_type = data.get('scan_type', 'unknown')
        target = data.get('target', 'unknown')
        self.logger.info(f"🎵 R2 chirped: Starting {scan_type} scan on {target}")
    
    async def _on_device_discovered(self, event) -> None:
        """Handle device discovered event"""
        await self.play_sound('device_found')
        # Log the discovery for user feedback
        data = event.data
        ip = data.get('ip', 'unknown')
        method = data.get('discovery_method', 'unknown')
        self.logger.info(f"🎵 R2 chirped: Device found at {ip} via {method}")
    
    async def _on_scan_completed(self, event) -> None:
        """Handle network scan completed event"""
        await self.play_sound('scan_complete')
        # Log completion with statistics
        data = event.data
        devices_found = data.get('devices_found', 0)
        scan_type = data.get('scan_type', 'unknown')
        self.logger.info(f"🎵 R2 chirped: {scan_type} scan complete - {devices_found} devices found")
    
    async def _on_scan_error(self, event) -> None:
        """Handle network scan error event"""
        await self.play_sound('scan_error')
        # Log error details
        data = event.data
        error = data.get('error', 'unknown error')
        self.logger.info(f"🎵 R2 chirped: Scan error - {error}")
    
    async def _on_device_analyzed(self, event) -> None:
        """Handle device analyzed event"""
        data = event.data
        analysis_type = data.get('analysis_type', 'unknown')
        
        if analysis_type == 'port_discovery':
            await self.play_sound('port_found')
            ports = data.get('open_ports', [])
            ip = data.get('ip', 'unknown')
            self.logger.info(f"🎵 R2 chirped: Open ports found on {ip} - {ports}")
        else:
            await self.play_sound('analyzing')
            self.logger.info(f"🎵 R2 chirped: Analyzing device - {analysis_type}")
    
    async def _on_system_startup(self, event) -> None:
        """Handle system startup event"""
        # Startup sound is already played in start() method
        self.logger.info("System startup event received")
    
    async def _on_system_shutdown(self, event) -> None:
        """Handle system shutdown event"""
        await self.play_sound('shutdown')