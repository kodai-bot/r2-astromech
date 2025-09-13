"""
R2 Communication Translator

Handles translation between human language and R2-style communication,
integrating with AI models and sound generation systems.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
import random
from datetime import datetime

from .model_manager import ModelManager

logger = logging.getLogger(__name__)


class R2Translator:
    """
    Handles translation between human language and R2-style communication.
    
    This class provides:
    - Human-to-R2 translation
    - R2-to-human interpretation
    - Context-aware communication
    - Integration with AI models and sound systems
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        """
        Initialize the R2 translator.
        
        Args:
            model_manager: Optional model manager instance
        """
        self.model_manager = model_manager or ModelManager()
        self.conversation_history: List[Dict] = []
        self.context_memory: Dict[str, any] = {}
        
        # Extended R2 sound vocabulary
        self.sound_patterns = {
            # Basic sounds
            'beep': {'type': 'short', 'tone': 'mid', 'emotion': 'neutral'},
            'boop': {'type': 'short', 'tone': 'low', 'emotion': 'calm'},
            'whistle': {'type': 'long', 'tone': 'high', 'emotion': 'alert'},
            'warble': {'type': 'medium', 'tone': 'varied', 'emotion': 'complex'},
            'chirp': {'type': 'short', 'tone': 'high', 'emotion': 'happy'},
            'trill': {'type': 'medium', 'tone': 'high', 'emotion': 'excited'},
            
            # Complex patterns
            'ascending-whistle': {'type': 'long', 'tone': 'rising', 'emotion': 'curious'},
            'descending-warble': {'type': 'medium', 'tone': 'falling', 'emotion': 'disappointed'},
            'rapid-beeps': {'type': 'burst', 'tone': 'mid', 'emotion': 'urgent'},
            'questioning-chirp': {'type': 'short', 'tone': 'rising', 'emotion': 'confused'},
            'triumphant-trill': {'type': 'long', 'tone': 'high', 'emotion': 'victorious'},
            'worried-warble': {'type': 'medium', 'tone': 'low', 'emotion': 'concerned'},
            
            # Special patterns
            'error-buzz': {'type': 'harsh', 'tone': 'low', 'emotion': 'error'},
            'processing-hum': {'type': 'continuous', 'tone': 'steady', 'emotion': 'thinking'},
            'shutdown-descend': {'type': 'long', 'tone': 'descending', 'emotion': 'sleepy'},
            'startup-ascend': {'type': 'long', 'tone': 'ascending', 'emotion': 'awakening'}
        }
        
        # Emotion to sound mapping
        self.emotion_sounds = {
            'happy': ['chirp-beep', 'trill-whistle', 'ascending-whistle'],
            'excited': ['rapid-beeps', 'triumphant-trill', 'chirp-chirp-beep!'],
            'sad': ['descending-warble', 'low-boop', 'mournful-whistle'],
            'confused': ['questioning-chirp?', 'warble-beep?', 'tilted-whistle?'],
            'angry': ['harsh-beep!', 'angry-buzz!', 'sharp-warble!'],
            'tired': ['slow-boop', 'weary-warble', 'shutdown-descend'],
            'alert': ['sharp-beep!', 'urgent-whistle!', 'rapid-chirps!'],
            'thinking': ['processing-hum...', 'contemplative-warble...', 'analyzing-beep...'],
            'agreeing': ['affirmative-beep', 'confirming-chirp', 'positive-trill'],
            'disagreeing': ['negative-warble', 'declining-beep', 'refusing-buzz'],
            'greeting': ['friendly-beep', 'welcoming-whistle', 'hello-chirp'],
            'farewell': ['goodbye-warble', 'departing-trill', 'see-you-beep']
        }
        
        # Context keywords for better translation
        self.context_keywords = {
            'technical': ['repair', 'fix', 'malfunction', 'system', 'diagnostic', 'error'],
            'social': ['hello', 'goodbye', 'friend', 'thanks', 'please', 'sorry'],
            'urgency': ['urgent', 'emergency', 'quick', 'fast', 'help', 'now'],
            'location': ['where', 'here', 'there', 'location', 'coordinates', 'map'],
            'time': ['when', 'now', 'later', 'time', 'schedule', 'wait'],
            'quantity': ['how many', 'count', 'number', 'few', 'many', 'all']
        }
    
    def translate_to_r2(self, human_text: str, context: Optional[Dict] = None) -> str:
        """
        Translate human text to R2-style communication.
        
        Args:
            human_text: Human text to translate
            context: Optional context information
            
        Returns:
            str: R2-style sound representation
        """
        try:
            # Store conversation
            self._add_to_history('human', human_text, context)
            
            # Analyze the input
            emotion = self._analyze_emotion(human_text)
            context_type = self._analyze_context(human_text)
            urgency = self._analyze_urgency(human_text)
            
            # Use AI model if available for more sophisticated translation
            if self.model_manager.get_current_model() is not None:
                ai_translation = self.model_manager.translate_to_r2(human_text)
                # Enhance AI translation with our analysis
                enhanced_translation = self._enhance_translation(
                    ai_translation, emotion, context_type, urgency
                )
                r2_response = enhanced_translation
            else:
                # Fallback to rule-based translation
                r2_response = self._rule_based_translation(human_text, emotion, context_type, urgency)
            
            # Store R2 response
            self._add_to_history('r2', r2_response, {
                'emotion': emotion,
                'context_type': context_type,
                'urgency': urgency
            })
            
            return r2_response
            
        except Exception as e:
            logger.error(f"Error in R2 translation: {e}")
            return "error-buzz"  # Default error sound
    
    def translate_from_r2(self, r2_sounds: str, context: Optional[Dict] = None) -> str:
        """
        Translate R2 sounds to human-readable interpretation.
        
        Args:
            r2_sounds: R2 sound pattern
            context: Optional context information
            
        Returns:
            str: Human-readable interpretation
        """
        try:
            # Store conversation
            self._add_to_history('r2', r2_sounds, context)
            
            # Use AI model if available
            if self.model_manager.get_current_model() is not None:
                interpretation = self.model_manager.translate_from_r2(r2_sounds)
            else:
                # Fallback to rule-based interpretation
                interpretation = self._rule_based_interpretation(r2_sounds)
            
            # Store interpretation
            self._add_to_history('human_interpretation', interpretation)
            
            return interpretation
            
        except Exception as e:
            logger.error(f"Error interpreting R2 sounds: {e}")
            return "Unable to interpret R2 communication."
    
    def _analyze_emotion(self, text: str) -> str:
        """Analyze the emotional content of text."""
        text_lower = text.lower()
        
        # Emotional keyword mapping
        emotion_keywords = {
            'excited': ['amazing', 'awesome', 'fantastic', 'incredible', 'wow'],
            'happy': ['good', 'great', 'nice', 'pleased', 'glad', 'thanks'],
            'sad': ['sad', 'disappointed', 'sorry', 'bad', 'terrible', 'awful'],
            'angry': ['angry', 'mad', 'frustrated', 'annoyed', 'furious'],
            'confused': ['confused', 'unclear', 'what', 'how', 'why', '?'],
            'tired': ['tired', 'exhausted', 'sleepy', 'weary'],
            'alert': ['alert', 'warning', 'danger', 'careful', 'watch out'],
            'thinking': ['think', 'consider', 'maybe', 'perhaps', 'wondering'],
            'agreeing': ['yes', 'agree', 'correct', 'right', 'exactly'],
            'disagreeing': ['no', 'wrong', 'disagree', 'incorrect', 'never']
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        return 'neutral'
    
    def _analyze_context(self, text: str) -> str:
        """Analyze the contextual type of the text."""
        text_lower = text.lower()
        
        for context_type, keywords in self.context_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return context_type
        
        return 'general'
    
    def _analyze_urgency(self, text: str) -> str:
        """Analyze the urgency level of the text."""
        text_lower = text.lower()
        urgent_indicators = ['!', 'urgent', 'emergency', 'quick', 'fast', 'now', 'asap']
        
        if any(indicator in text_lower for indicator in urgent_indicators):
            return 'high'
        elif any(word in text_lower for word in ['slow', 'wait', 'later', 'eventually']):
            return 'low'
        else:
            return 'medium'
    
    def _enhance_translation(self, ai_translation: str, emotion: str, 
                           context_type: str, urgency: str) -> str:
        """Enhance AI translation with additional analysis."""
        # Add urgency indicators
        if urgency == 'high':
            ai_translation = ai_translation.replace('beep', 'urgent-beep!')
            ai_translation = ai_translation.replace('!', '!!')
        
        # Add emotional context if not present
        if emotion in self.emotion_sounds and not any(
            sound in ai_translation for sound in self.emotion_sounds[emotion]
        ):
            # Blend emotional sound with AI translation
            emotion_sound = random.choice(self.emotion_sounds[emotion])
            ai_translation = f"{emotion_sound} {ai_translation}"
        
        return ai_translation
    
    def _rule_based_translation(self, text: str, emotion: str, 
                              context_type: str, urgency: str) -> str:
        """Rule-based fallback translation."""
        # Select base sounds based on emotion
        if emotion in self.emotion_sounds:
            base_sounds = self.emotion_sounds[emotion]
        else:
            base_sounds = ['beep-boop', 'chirp-whistle', 'warble-trill']
        
        selected_sound = random.choice(base_sounds)
        
        # Modify based on urgency
        if urgency == 'high':
            selected_sound = selected_sound.replace('-', '-urgent-')
            if not selected_sound.endswith('!'):
                selected_sound += '!'
        elif urgency == 'low':
            selected_sound = selected_sound.replace('-', '-slow-')
            if selected_sound.endswith('!'):
                selected_sound = selected_sound[:-1]
        
        # Add context-specific modifications
        if context_type == 'technical':
            selected_sound = f"diagnostic-{selected_sound}"
        elif context_type == 'social':
            selected_sound = f"friendly-{selected_sound}"
        
        return selected_sound
    
    def _rule_based_interpretation(self, r2_sounds: str) -> str:
        """Rule-based interpretation of R2 sounds."""
        sound_lower = r2_sounds.lower()
        
        # Pattern matching for interpretation
        if 'error' in sound_lower or 'buzz' in sound_lower:
            return "R2 is indicating an error or malfunction."
        elif 'urgent' in sound_lower or '!!' in sound_lower:
            return "R2 is expressing something urgent or important."
        elif 'happy' in sound_lower or 'chirp' in sound_lower:
            return "R2 sounds happy and content."
        elif 'sad' in sound_lower or 'descending' in sound_lower:
            return "R2 seems sad or disappointed."
        elif '?' in sound_lower:
            return "R2 is asking a question or expressing confusion."
        elif 'processing' in sound_lower or 'hum' in sound_lower:
            return "R2 is thinking or processing information."
        else:
            return "R2 is communicating something."
    
    def _add_to_history(self, speaker: str, message: str, context: Optional[Dict] = None):
        """Add message to conversation history."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'speaker': speaker,
            'message': message,
            'context': context or {}
        }
        self.conversation_history.append(entry)
        
        # Keep only last 50 entries to prevent memory bloat
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent conversation history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of conversation entries
        """
        return self.conversation_history[-limit:]
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def set_context_memory(self, key: str, value: any):
        """Set a context memory value."""
        self.context_memory[key] = value
    
    def get_context_memory(self, key: str, default: any = None) -> any:
        """Get a context memory value."""
        return self.context_memory.get(key, default)
    
    def generate_contextual_response(self, input_text: str) -> Tuple[str, str]:
        """
        Generate both R2 sounds and human interpretation.
        
        Args:
            input_text: Human input text
            
        Returns:
            Tuple of (r2_sounds, human_interpretation)
        """
        # Generate R2 response
        r2_sounds = self.translate_to_r2(input_text)
        
        # Generate interpretation of R2's response
        interpretation = self.translate_from_r2(r2_sounds)
        
        return r2_sounds, interpretation
    
    def get_sound_patterns(self) -> Dict[str, Dict]:
        """Get available sound patterns."""
        return self.sound_patterns.copy()
    
    def get_available_emotions(self) -> List[str]:
        """Get list of available emotions."""
        return list(self.emotion_sounds.keys())
