"""
Modular Phi-3 Model Implementation

This module implements the Phi-3 model for the new modular R2 system.
It provides natural language processing and R2 communication translation.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import logging
from typing import Dict, Any, Optional, List
import re
import random
from datetime import datetime

from ..interfaces import IAIModel

logger = logging.getLogger(__name__)


class ModularPhi3Model(IAIModel):
    """
    Modular Phi-3 model implementation for R2 astromech communication.
    
    This class wraps the Microsoft Phi-3 model to provide:
    - Natural language understanding
    - R2-style communication translation
    - Context-aware responses
    - Event-driven integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize modular Phi-3 model.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        self.config = config
        self.logger = logger
        
        # Model configuration
        self.model_name = "phi-3"
        self.device = config.get('device', 'cpu')
        self.model_path = config.get('model_path', 'microsoft/Phi-3-mini-4k-instruct')
        self.max_length = config.get('max_length', 512)
        self.temperature = config.get('temperature', 0.7)
        
        # Event bus for communication
        self.event_bus = config.get('event_bus')
        
        # Model components
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        # R2-specific sound mappings
        self.r2_sounds = {
            'excited': ['beep-boop-beep!', 'whistle-beep!', 'warble-chirp!'],
            'happy': ['beep-beep-boop', 'chirp-whistle', 'trill-beep'],
            'confused': ['boop-beep?', 'warble?', 'questioning-chirp?'],
            'sad': ['low-warble', 'sad-beep', 'mournful-whistle'],
            'alert': ['urgent-beep-beep!', 'warning-chirp!', 'alarm-warble!'],
            'curious': ['curious-beep', 'investigating-chirp', 'scanning-trill'],
            'confident': ['confident-beep', 'assured-chirp', 'decisive-trill'],
            'helpful': ['helpful-beep', 'assisting-chirp', 'supportive-trill'],
            'playful': ['playful-beep', 'cheeky-chirp', 'mischievous-trill'],
            'cautious': ['cautious-beep', 'careful-chirp', 'wary-trill']
        }
        
        # Emotion detection patterns
        self.emotion_patterns = {
            'excited': ['excited', 'thrilled', 'amazing', 'incredible', 'wow'],
            'happy': ['happy', 'glad', 'pleased', 'good', 'great', 'wonderful'],
            'confused': ['confused', 'unclear', 'unsure', 'puzzled', 'mystery'],
            'sad': ['sad', 'disappointed', 'sorry', 'unfortunate', 'tragic'],
            'alert': ['alert', 'warning', 'danger', 'threat', 'urgent', 'critical'],
            'curious': ['curious', 'interesting', 'wonder', 'investigate', 'explore'],
            'confident': ['confident', 'sure', 'certain', 'definitely', 'absolutely'],
            'helpful': ['help', 'assist', 'support', 'aid', 'guide'],
            'playful': ['fun', 'playful', 'cheeky', 'mischievous', 'tease'],
            'cautious': ['careful', 'cautious', 'wary', 'careful', 'prudent']
        }
        
        # R2 personality traits
        self.personality_mode = config.get('personality_mode', 'helpful')
        self.response_style = config.get('response_style', 'concise')
        
        # Context management
        self.conversation_history = []
        self.max_history = config.get('context_window', 10)
        
        self.logger.info(f"Modular Phi-3 model initialized")
    
    async def load_model(self) -> bool:
        """
        Load the Phi-3 model.
        
        Returns:
            bool: True if loaded successfully
        """
        try:
            self.logger.info(f"Loading Phi-3 model from {self.model_path}")
            
            # Configure quantization for efficiency
            quantization_config = None
            if self.device == 'cuda' and torch.cuda.is_available():
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            model_kwargs = {
                'trust_remote_code': True,
                'torch_dtype': torch.float16 if self.device == 'cuda' else torch.float32
            }
            
            if quantization_config:
                model_kwargs['quantization_config'] = quantization_config
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                **model_kwargs
            )
            
            # Move to device
            if self.device == 'cuda' and torch.cuda.is_available():
                self.model = self.model.to('cuda')
            
            self.is_loaded = True
            self.logger.info("Phi-3 model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load Phi-3 model: {e}")
            return False
    
    async def unload_model(self) -> bool:
        """
        Unload the Phi-3 model.
        
        Returns:
            bool: True if unloaded successfully
        """
        try:
            if self.model:
                del self.model
                self.model = None
            
            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None
            
            # Clear GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.is_loaded = False
            self.logger.info("Phi-3 model unloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload Phi-3 model: {e}")
            return False
    
    async def generate_response(self, input_text: str, **kwargs) -> str:
        """
        Generate response from the Phi-3 model.
        
        Args:
            input_text: Input text
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        try:
            if not self.is_loaded:
                raise RuntimeError("Model not loaded")
            
            # Add to conversation history
            self.conversation_history.append({
                'timestamp': datetime.now(),
                'input': input_text,
                'type': 'user_input'
            })
            
            # Limit history size
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            # Create context-aware prompt
            prompt = self._create_contextual_prompt(input_text)
            
            # Generate response
            response = await self._generate_with_model(prompt, **kwargs)
            
            # Add response to history
            self.conversation_history.append({
                'timestamp': datetime.now(),
                'response': response,
                'type': 'ai_response'
            })
            
            # Publish response generated event
            if self.event_bus:
                await self.event_bus.publish(create_event(
                    R2Events.AI_RESPONSE_GENERATED,
                    {
                        "input": input_text[:100] + "..." if len(input_text) > 100 else input_text,
                        "response": response[:100] + "..." if len(response) > 100 else response,
                        "model_name": self.model_name
                    },
                    self.model_name
                ))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"
    
    async def translate_to_r2(self, human_text: str) -> str:
        """
        Translate human text to R2 sounds.
        
        Args:
            human_text: Human text
            
        Returns:
            str: R2 sound representation
        """
        try:
            # Detect emotion in text
            emotion = self._detect_emotion(human_text)
            
            # Get appropriate R2 sounds
            sounds = self.r2_sounds.get(emotion, self.r2_sounds['curious'])
            
            # Add randomization based on personality
            if self.personality_mode == 'playful':
                # More variation for playful personality
                base_sound = random.choice(sounds)
                variations = ['beep', 'boop', 'chirp', 'whistle', 'trill', 'warble']
                additional_sounds = random.sample(variations, random.randint(1, 2))
                return f"{base_sound}-{'-'.join(additional_sounds)}"
            else:
                # Standard variation
                return random.choice(sounds)
            
        except Exception as e:
            self.logger.error(f"Error translating to R2: {e}")
            return "error-beep"
    
    async def translate_from_r2(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text.
        
        Args:
            r2_sounds: R2 sound pattern
            
        Returns:
            str: Human interpretation
        """
        try:
            # Analyze sound pattern
            sound_analysis = self._analyze_r2_sounds(r2_sounds)
            
            # Generate human interpretation
            interpretation = self._generate_human_interpretation(sound_analysis)
            
            return interpretation
            
        except Exception as e:
            self.logger.error(f"Error translating from R2: {e}")
            return "R2 communication error"
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "name": self.model_name,
            "type": "Phi-3",
            "model_path": self.model_path,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "personality_mode": self.personality_mode,
            "response_style": self.response_style,
            "capabilities": [
                "Natural language understanding",
                "R2 sound translation",
                "Context-aware responses",
                "Emotion detection",
                "Conversation management"
            ],
            "conversation_history_length": len(self.conversation_history),
            "memory_usage": self._get_model_memory_usage()
        }
    
    def _create_contextual_prompt(self, input_text: str) -> str:
        """Create a context-aware prompt for the model"""
        # Base system prompt
        system_prompt = f"""You are R2-D2, the beloved astromech droid from Star Wars. 
You are {self.personality_mode} and should respond in character. 
Keep responses {self.response_style} and in R2's personality.
"""
        
        # Add conversation context
        if self.conversation_history:
            context = "\nRecent conversation:\n"
            for entry in self.conversation_history[-3:]:  # Last 3 exchanges
                if entry['type'] == 'user_input':
                    context += f"Human: {entry['input']}\n"
                elif entry['type'] == 'ai_response':
                    context += f"R2: {entry['response']}\n"
            system_prompt += context
        
        # Add current input
        system_prompt += f"\nHuman: {input_text}\nR2:"
        
        return system_prompt
    
    async def _generate_with_model(self, prompt: str, **kwargs) -> str:
        """Generate response using the actual model"""
        try:
            # Prepare input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if self.device == 'cuda' and torch.cuda.is_available():
                inputs = inputs.to('cuda')
            
            # Generation parameters
            generation_params = {
                'max_length': self.max_length,
                'temperature': self.temperature,
                'do_sample': True,
                'pad_token_id': self.tokenizer.eos_token_id,
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 50)
            }
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    **generation_params
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new response part
            if "R2:" in response:
                response = response.split("R2:")[-1].strip()
            
            # Clean up response
            response = self._clean_response(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in model generation: {e}")
            return f"Model generation error: {e}"
    
    def _detect_emotion(self, text: str) -> str:
        """Detect emotion in text"""
        text_lower = text.lower()
        
        # Score each emotion
        emotion_scores = {}
        for emotion, patterns in self.emotion_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            emotion_scores[emotion] = score
        
        # Return emotion with highest score, default to curious
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        return 'curious'
    
    def _analyze_r2_sounds(self, sounds: str) -> Dict[str, Any]:
        """Analyze R2 sound patterns"""
        analysis = {
            'emotion': 'curious',
            'intensity': 'medium',
            'complexity': 'simple'
        }
        
        # Analyze sound components
        sound_components = sounds.lower().split('-')
        
        # Determine emotion based on sound components
        if any(sound in sounds.lower() for sound in ['excited', 'thrilled', 'amazing']):
            analysis['emotion'] = 'excited'
        elif any(sound in sounds.lower() for sound in ['urgent', 'warning', 'alarm']):
            analysis['emotion'] = 'alert'
        elif any(sound in sounds.lower() for sound in ['sad', 'mournful']):
            analysis['emotion'] = 'sad'
        elif any(sound in sounds.lower() for sound in ['playful', 'cheeky', 'mischievous']):
            analysis['emotion'] = 'playful'
        
        # Determine intensity
        if '!' in sounds:
            analysis['intensity'] = 'high'
        elif '?' in sounds:
            analysis['intensity'] = 'low'
        
        # Determine complexity
        if len(sound_components) > 3:
            analysis['complexity'] = 'complex'
        elif len(sound_components) > 1:
            analysis['complexity'] = 'medium'
        
        return analysis
    
    def _generate_human_interpretation(self, analysis: Dict[str, Any]) -> str:
        """Generate human interpretation of R2 sounds"""
        emotion = analysis['emotion']
        intensity = analysis['intensity']
        complexity = analysis['complexity']
        
        interpretations = {
            'excited': {
                'high': "R2 is very excited and enthusiastic!",
                'medium': "R2 is excited about something!",
                'low': "R2 seems pleased."
            },
            'alert': {
                'high': "R2 is sounding urgent alarms!",
                'medium': "R2 is alerting about something important.",
                'low': "R2 is being cautious."
            },
            'curious': {
                'high': "R2 is very curious and investigating!",
                'medium': "R2 is curious about something.",
                'low': "R2 is mildly interested."
            },
            'sad': {
                'high': "R2 is very sad and mournful.",
                'medium': "R2 seems disappointed.",
                'low': "R2 is a bit down."
            },
            'playful': {
                'high': "R2 is being very playful and mischievous!",
                'medium': "R2 is being playful.",
                'low': "R2 is in a good mood."
            }
        }
        
        base_interpretation = interpretations.get(emotion, interpretations['curious'])[intensity]
        
        if complexity == 'complex':
            base_interpretation += " The communication is quite complex."
        
        return base_interpretation
    
    def _clean_response(self, response: str) -> str:
        """Clean up model response"""
        # Remove any remaining prompt text
        if "Human:" in response:
            response = response.split("Human:")[0]
        
        # Remove extra whitespace
        response = response.strip()
        
        # Ensure response ends properly
        if not response.endswith(('.', '!', '?')):
            response += '.'
        
        return response
    
    def _get_model_memory_usage(self) -> Dict[str, Any]:
        """Get model memory usage information"""
        memory_info = {}
        
        if torch.cuda.is_available():
            memory_info['gpu_memory_mb'] = torch.cuda.memory_allocated() // (1024 * 1024)
            memory_info['gpu_memory_reserved_mb'] = torch.cuda.memory_reserved() // (1024 * 1024)
        
        return memory_info