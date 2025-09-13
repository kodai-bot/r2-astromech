"""
Personality Module Interfaces

This module defines the interfaces for R2's personality system
including audio engine, sound generation, and personality management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ...core.interfaces import IModule


class IAudioEngine(IModule):
    """Audio Engine interface"""
    
    @abstractmethod
    async def play_sound(self, sound_id: str, volume: float = 0.7) -> bool:
        """
        Play a sound by ID.
        
        Args:
            sound_id: Sound identifier
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if sound played successfully
        """
        pass
    
    @abstractmethod
    async def play_sequence(self, sequence: List[str], volume: float = 0.7) -> bool:
        """
        Play a sequence of sounds.
        
        Args:
            sequence: List of sound IDs
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if sequence played successfully
        """
        pass
    
    @abstractmethod
    async def play_letter_sequence(self, letters: str, volume: float = 0.7) -> bool:
        """
        Play a sequence of letter sounds.
        
        Args:
            letters: Space-separated letter sequence (e.g., "a b c")
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if sequence played successfully
        """
        pass
    
    @abstractmethod
    async def stop_audio(self) -> bool:
        """
        Stop all audio playback.
        
        Returns:
            bool: True if stopped successfully
        """
        pass
    
    @abstractmethod
    async def get_available_sounds(self) -> List[str]:
        """
        Get list of available sound IDs.
        
        Returns:
            List[str]: Available sound IDs
        """
        pass
    
    @abstractmethod
    async def get_available_letters(self) -> List[str]:
        """
        Get list of available letter sounds.
        
        Returns:
            List[str]: Available letter sounds
        """
        pass
    
    @abstractmethod
    async def set_volume(self, volume: float) -> bool:
        """
        Set global volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if volume set successfully
        """
        pass
    
    @abstractmethod
    async def get_volume(self) -> float:
        """
        Get current volume level.
        
        Returns:
            float: Current volume level
        """
        pass


class ISoundGenerator(IModule):
    """Sound Generation interface"""
    
    @abstractmethod
    async def generate_sound_from_text(self, text: str, emotion: Optional[str] = None) -> str:
        """
        Generate sound sequence from text.
        
        Args:
            text: Input text
            emotion: Optional emotion context
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def generate_emotion_sound(self, emotion: str, intensity: float = 0.5) -> str:
        """
        Generate sound for specific emotion.
        
        Args:
            emotion: Emotion name
            intensity: Emotion intensity (0.0 to 1.0)
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def generate_response_sound(self, context: str, response_type: str) -> str:
        """
        Generate sound for system response.
        
        Args:
            context: Response context
            response_type: Type of response (success, error, warning, etc.)
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def add_vocabulary(self, event: str, sound_sequence: str) -> bool:
        """
        Add new vocabulary entry.
        
        Args:
            event: Event name
            sound_sequence: Sound sequence for the event
            
        Returns:
            bool: True if added successfully
        """
        pass
    
    @abstractmethod
    async def get_vocabulary(self) -> Dict[str, str]:
        """
        Get current vocabulary.
        
        Returns:
            Dict[str, str]: Event to sound sequence mapping
        """
        pass


class IPersonalityManager(IModule):
    """Personality Manager interface"""
    
    @abstractmethod
    async def express_emotion(self, emotion: str, context: str, intensity: float = 0.5) -> str:
        """
        Express emotion through sounds.
        
        Args:
            emotion: Emotion to express
            context: Context for the emotion
            intensity: Emotion intensity (0.0 to 1.0)
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def respond_to_event(self, event: str, data: Dict[str, Any]) -> str:
        """
        Respond to system event with appropriate sounds.
        
        Args:
            event: Event name
            data: Event data
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def respond_to_scan_result(self, devices_found: int, errors: int = 0) -> str:
        """
        Respond to network scan results.
        
        Args:
            devices_found: Number of devices found
            errors: Number of errors encountered
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def respond_to_ai_analysis(self, analysis_type: str, result: Dict[str, Any]) -> str:
        """
        Respond to AI analysis results.
        
        Args:
            analysis_type: Type of analysis performed
            result: Analysis results
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def set_personality_mode(self, mode: str) -> bool:
        """
        Set personality mode.
        
        Args:
            mode: Personality mode (helpful, cheeky, curious, cautious)
            
        Returns:
            bool: True if mode set successfully
        """
        pass
    
    @abstractmethod
    async def get_personality_mode(self) -> str:
        """
        Get current personality mode.
        
        Returns:
            str: Current personality mode
        """
        pass
    
    @abstractmethod
    async def get_available_emotions(self) -> List[str]:
        """
        Get available emotions.
        
        Returns:
            List[str]: Available emotions
        """
        pass


class IVoiceSynthesizer(IModule):
    """Voice Synthesis interface (for future text-to-speech)"""
    
    @abstractmethod
    async def synthesize_speech(self, text: str, voice: str = "r2") -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            
        Returns:
            bytes: Audio data
        """
        pass
    
    @abstractmethod
    async def synthesize_r2_speech(self, r2_sounds: str) -> bytes:
        """
        Synthesize R2-style speech from sound sequence.
        
        Args:
            r2_sounds: R2 sound sequence
            
        Returns:
            bytes: Audio data
        """
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> List[str]:
        """
        Get available voices.
        
        Returns:
            List[str]: Available voice names
        """
        pass


class IEmotionAnalyzer(IModule):
    """Emotion Analysis interface"""
    
    @abstractmethod
    async def analyze_text_emotion(self, text: str) -> Dict[str, float]:
        """
        Analyze emotion in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict[str, float]: Emotion scores
        """
        pass
    
    @abstractmethod
    async def analyze_context_emotion(self, context: str, data: Dict[str, Any]) -> str:
        """
        Analyze emotion from context and data.
        
        Args:
            context: Context description
            data: Context data
            
        Returns:
            str: Dominant emotion
        """
        pass
    
    @abstractmethod
    async def get_emotion_from_scan_results(self, devices_found: int, errors: int) -> str:
        """
        Determine emotion from scan results.
        
        Args:
            devices_found: Number of devices found
            errors: Number of errors
            
        Returns:
            str: Appropriate emotion
        """
        pass