#!/usr/bin/env python3
"""
R2 AI Integration Example

Demonstrates how to integrate the AI system with the existing R2 personality
and sound systems for a complete R2 experience.
"""

import sys
import os
import time

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.ai.model_manager import ModelManager
from src.ai.translator import R2Translator
from src.personality.r2_sounds import R2Sounds


class R2AIDroid:
    """
    Complete R2 droid with AI integration.
    
    Combines AI language processing with R2 personality and sound generation.
    """
    
    def __init__(self):
        """Initialize R2 with AI capabilities."""
        print("🤖 Initializing R2-D2 with AI capabilities...")
        
        # Initialize AI components
        self.ai_manager = ModelManager()
        self.translator = R2Translator(self.ai_manager)
        
        # Initialize R2 personality/sounds
        try:
            self.sounds = R2Sounds()
            self.has_audio = True
            print("✓ Audio system initialized")
        except Exception as e:
            print(f"⚠ Audio system not available: {e}")
            self.has_audio = False
        
        # Try to load AI model
        print("Loading AI model (this may take a moment)...")
        self.ai_loaded = self.ai_manager.load_model('phi-3')
        
        if self.ai_loaded:
            print("✓ AI model loaded successfully!")
        else:
            print("⚠ Using rule-based responses (AI model not available)")
        
        print("🤖 R2-D2 is ready!")
    
    def respond_to_human(self, human_input: str) -> None:
        """
        Respond to human input with both R2 sounds and optional AI-generated text.
        
        Args:
            human_input: What the human said to R2
        """
        print(f"\n👤 Human: {human_input}")
        
        # Generate R2 response using AI
        r2_sounds, interpretation = self.translator.generate_contextual_response(human_input)
        
        print(f"🤖 R2: {r2_sounds}")
        print(f"💭 (Translation: {interpretation})")
        
        # Play actual sounds if available
        if self.has_audio:
            try:
                self._play_r2_sounds(r2_sounds)
            except Exception as e:
                print(f"⚠ Could not play audio: {e}")
        
        # If AI is loaded, also generate a more detailed response
        if self.ai_loaded:
            try:
                ai_response = self.ai_manager.generate_response(human_input)
                if ai_response and ai_response != human_input:
                    print(f"🧠 (AI thoughts: {ai_response})")
            except Exception as e:
                print(f"⚠ AI response error: {e}")
    
    def _play_r2_sounds(self, r2_sounds: str) -> None:
        """
        Convert R2 sound description to actual audio playback.
        
        Args:
            r2_sounds: R2 sound pattern description
        """
        # Parse the sound description and map to available sound files
        sound_mapping = {
            'beep': ['beep', 'b.wav'],
            'boop': ['boop', 'o.wav'], 
            'chirp': ['chirp', 'c.wav'],
            'whistle': ['whistle', 'w.wav'],
            'warble': ['warble', 'r.wav'],
            'trill': ['trill', 't.wav']
        }
        
        # Extract base sounds from the description
        sounds_to_play = []
        for sound_name, file_options in sound_mapping.items():
            if sound_name in r2_sounds.lower():
                sounds_to_play.extend(file_options[:1])  # Take first option
        
        # If no specific sounds found, play a default sequence
        if not sounds_to_play:
            sounds_to_play = ['b.wav', 'o.wav']  # Default beep-boop
        
        # Play the sounds
        print(f"🔊 Playing sounds: {sounds_to_play}")
        for sound in sounds_to_play:
            try:
                self.sounds.play_sound(sound)
                time.sleep(0.3)  # Small delay between sounds
            except:
                # If specific sound fails, try a generic one
                self.sounds.play_sound('b.wav')
    
    def diagnostic_mode(self) -> None:
        """Run R2 in diagnostic mode - report system status."""
        print("\n🔧 R2 Diagnostic Mode")
        
        # Check AI system
        ai_status = self.ai_manager.get_model_status()
        self.respond_to_human("Run system diagnostic")
        
        print(f"\n📊 System Status:")
        print(f"   AI Model: {'Loaded' if ai_status['loaded'] else 'Not loaded'}")
        print(f"   Audio: {'Available' if self.has_audio else 'Not available'}")
        print(f"   Available Models: {ai_status['available_models']}")
        
        if ai_status['loaded']:
            model_info = ai_status['model_info']
            print(f"   Current Model: {model_info['name']}")
            print(f"   Model Config: {model_info['config'].get('device', 'unknown')}")
    
    def conversation_mode(self) -> None:
        """Interactive conversation mode with R2."""
        print("\n💬 R2 Conversation Mode")
        print("Talk to R2! Type 'exit' to quit, 'diagnostic' for system status")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    self.respond_to_human("Goodbye!")
                    break
                
                if user_input.lower() == 'diagnostic':
                    self.diagnostic_mode()
                    continue
                
                self.respond_to_human(user_input)
                
            except KeyboardInterrupt:
                print("\n\n🤖 R2: goodbye-warble")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def demo_scenarios(self) -> None:
        """Demonstrate various R2 interaction scenarios."""
        print("\n🎬 R2 Demo Scenarios")
        
        scenarios = [
            "Hello R2, nice to meet you!",
            "Can you help me repair this hyperdrive?", 
            "I'm feeling sad today",
            "That's incredible! Amazing work!",
            "Where did Princess Leia go?",
            "Emergency! Imperial troops are coming!",
            "Thank you for your help, R2",
            "I'm confused about these schematics"
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n--- Scenario {i} ---")
            self.respond_to_human(scenario)
            time.sleep(1)  # Pause between scenarios
    
    def shutdown(self) -> None:
        """Shutdown R2 systems."""
        print("\n🔄 Shutting down R2 systems...")
        
        self.respond_to_human("Powering down")
        
        # Unload AI model to free memory
        if self.ai_loaded:
            self.ai_manager.unload_current_model()
            print("✓ AI model unloaded")
        
        print("🤖 R2-D2 shutdown complete")


def main():
    """Main demo function."""
    print("R2-D2 AI Integration Demo")
    print("=" * 40)
    
    try:
        # Initialize R2
        r2 = R2AIDroid()
        
        # Show menu
        while True:
            print("\n🤖 R2-D2 Options:")
            print("1. Demo Scenarios")
            print("2. Conversation Mode")
            print("3. Diagnostic Mode")
            print("4. Shutdown")
            
            try:
                choice = input("\nSelect option (1-4): ").strip()
                
                if choice == '1':
                    r2.demo_scenarios()
                elif choice == '2':
                    r2.conversation_mode()
                elif choice == '3':
                    r2.diagnostic_mode()
                elif choice == '4':
                    r2.shutdown()
                    break
                else:
                    print("Invalid choice. Please select 1-4.")
                    
            except KeyboardInterrupt:
                r2.shutdown()
                break
    
    except Exception as e:
        print(f"Error initializing R2: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")


if __name__ == '__main__':
    main()
