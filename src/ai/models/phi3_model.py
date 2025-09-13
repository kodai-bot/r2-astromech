"""
Phi-3 Model Implementation

Microsoft Phi-3 model wrapper for the R2 astromech droid system.
Provides natural language processing and R2 communication translation.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
from typing import Dict, Any, Optional
import re
import random

from .base_model import BaseAIModel

logger = logging.getLogger(__name__)


class Phi3Model(BaseAIModel):
    """
    Phi-3 model implementation for R2 astromech communication.
    
    This class wraps the Microsoft Phi-3 model to provide:
    - Natural language understanding
    - R2-style communication translation
    - Context-aware responses
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Phi-3 model.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        super().__init__("phi-3", config)
        self.tokenizer = None
        self.model = None
        self.device = config.get('device', 'cpu')
        self.model_path = config.get('model_path', 'microsoft/Phi-3-mini-4k-instruct')
        self.max_length = config.get('max_length', 512)
        self.temperature = config.get('temperature', 0.7)
        
        # R2-specific sound mappings
        self.r2_sounds = {
            'excited': ['beep-boop-beep!', 'whistle-beep!', 'warble-chirp!'],
            'happy': ['beep-beep-boop', 'chirp-whistle', 'trill-beep'],
            'confused': ['boop-beep?', 'warble?', 'questioning-chirp?'],
            'sad': ['low-warble', 'sad-beep', 'mournful-whistle'],
            'angry': ['harsh-beep!', 'angry-warble!', 'sharp-chirp!'],
            'acknowledgment': ['beep-boop', 'affirmative-chirp', 'confirming-whistle'],
            'negative': ['negative-warble', 'disagreeing-beep', 'declining-chirp'],
            'thinking': ['contemplative-beep...', 'processing-warble...', 'analyzing-chirp...']
        }
        
    def load_model(self) -> bool:
        """
        Load the Phi-3 model and tokenizer.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading Phi-3 model from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                device_map=self.device if self.device == 'cuda' else None,
                trust_remote_code=True
            )
            
            if self.device == 'cpu':
                self.model = self.model.to('cpu')
            
            self.is_loaded = True
            logger.info("Phi-3 model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Phi-3 model: {e}")
            self.is_loaded = False
            return False
    
    def unload_model(self) -> bool:
        """
        Unload the Phi-3 model from memory.
        
        Returns:
            bool: True if unloaded successfully, False otherwise
        """
        try:
            if self.model is not None:
                del self.model
                self.model = None
            
            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.is_loaded = False
            logger.info("Phi-3 model unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload Phi-3 model: {e}")
            return False
    
    def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate a response using the Phi-3 model.
        
        Args:
            input_text: Input text to process
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated response
        """
        if not self.is_loaded:
            logger.error("Model not loaded. Call load_model() first.")
            return "Error: Model not loaded"
        
        try:
            # Prepare the prompt for R2-style communication
            system_prompt = """You are R2-D2, the beloved astromech droid from Star Wars. 
            You should respond in character, being helpful, curious, and sometimes a bit cheeky. 
            Keep responses concise and in R2's personality."""
            
            full_prompt = f"System: {system_prompt}\nHuman: {input_text}\nR2-D2:"
            
            # Tokenize input
            inputs = self.tokenizer.encode(full_prompt, return_tensors="pt").to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=kwargs.get('max_length', self.max_length),
                    temperature=kwargs.get('temperature', self.temperature),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the R2 response part
            if "R2-D2:" in response:
                response = response.split("R2-D2:")[-1].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {e}"
    
    def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2-style beeps and sounds.
        
        Args:
            human_text: Human text to translate
            
        Returns:
            str: R2-style sound representation
        """
        # Simple sentiment analysis based on keywords
        text_lower = human_text.lower()
        
        # Determine emotion/sentiment
        if any(word in text_lower for word in ['great', 'awesome', 'excellent', 'wonderful']):
            emotion = 'excited'
        elif any(word in text_lower for word in ['good', 'nice', 'thanks', 'thank you']):
            emotion = 'happy'
        elif any(word in text_lower for word in ['what', 'how', 'why', 'confused', '?']):
            emotion = 'confused'
        elif any(word in text_lower for word in ['sad', 'sorry', 'bad', 'terrible']):
            emotion = 'sad'
        elif any(word in text_lower for word in ['angry', 'mad', 'frustrated', 'annoying']):
            emotion = 'angry'
        elif any(word in text_lower for word in ['no', 'not', 'never', 'stop']):
            emotion = 'negative'
        elif any(word in text_lower for word in ['yes', 'ok', 'sure', 'agree']):
            emotion = 'acknowledgment'
        elif any(word in text_lower for word in ['think', 'consider', 'maybe', 'perhaps']):
            emotion = 'thinking'
        else:
            emotion = 'happy'  # Default to happy
        
        # Select appropriate R2 sound
        sounds = self.r2_sounds.get(emotion, self.r2_sounds['happy'])
        selected_sound = random.choice(sounds)
        
        return selected_sound
    
    def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2-style sounds to human-readable interpretation.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human-readable interpretation
        """
        # Reverse mapping from sounds to emotions
        sound_to_emotion = {}
        for emotion, sounds in self.r2_sounds.items():
            for sound in sounds:
                sound_to_emotion[sound] = emotion
        
        # Find the emotion for the given sound
        emotion = sound_to_emotion.get(r2_sounds, 'happy')
        
        # Generate interpretation based on emotion
        interpretations = {
            'excited': "R2 seems very excited and enthusiastic!",
            'happy': "R2 sounds pleased and content.",
            'confused': "R2 appears confused and is asking for clarification.",
            'sad': "R2 sounds disappointed or sad.",
            'angry': "R2 seems frustrated or annoyed.",
            'acknowledgment': "R2 is confirming or agreeing.",
            'negative': "R2 is expressing disagreement or refusal.",
            'thinking': "R2 is processing and thinking about something."
        }
        
        return interpretations.get(emotion, "R2 is communicating something.")
    
    def set_personality_mode(self, mode: str) -> bool:
        """
        Set R2's personality mode for responses.
        
        Args:
            mode: Personality mode ('helpful', 'cheeky', 'curious', 'cautious')
            
        Returns:
            bool: True if mode set successfully
        """
        valid_modes = ['helpful', 'cheeky', 'curious', 'cautious']
        if mode in valid_modes:
            self.config['personality_mode'] = mode
            logger.info(f"R2 personality mode set to: {mode}")
            return True
        else:
            logger.warning(f"Invalid personality mode: {mode}")
            return False
    
    def get_available_emotions(self) -> list:
        """
        Get list of available R2 emotions/sound types.
        
        Returns:
            list: Available emotion types
        """
        return list(self.r2_sounds.keys())
