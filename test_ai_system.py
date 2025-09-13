#!/usr/bin/env python3
"""
Test script for R2 Astromech AI System

This script demonstrates the AI functionality and can be used to test
the Phi-3 model integration without running the full astromech system.
"""

import sys
import os
import logging
from typing import Optional

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ai.model_manager import ModelManager
from src.ai.translator import R2Translator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_model_manager():
    """Test the model manager functionality."""
    print("\n=== Testing Model Manager ===")
    
    try:
        # Initialize model manager
        manager = ModelManager()
        print(f"✓ Model manager initialized")
        print(f"Available models: {manager.get_available_models()}")
        
        # Check initial memory usage
        memory_info = manager.get_memory_usage()
        print(f"Initial memory usage: {memory_info.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
        
        # Check status without loading
        status = manager.get_model_status()
        print(f"Initial status: {status}")
        
        # Try to load Phi-3 model (this might take time or fail if not available)
        print("Attempting to load Phi-3 model...")
        success = manager.load_model('phi-3')
        
        if success:
            print("✓ Phi-3 model loaded successfully!")
            
            # Check memory usage after loading
            memory_after = manager.get_memory_usage()
            print(f"Memory after loading: {memory_after.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
            
            if memory_after.get('gpu_memory'):
                for device, gpu_info in memory_after['gpu_memory'].items():
                    if isinstance(gpu_info, dict) and 'allocated_gb' in gpu_info:
                        print(f"GPU {device}: {gpu_info['allocated_gb']:.2f}GB allocated")
            
            # Test generation
            test_prompt = "Hello R2, how are you today?"
            print(f"Testing generation with: '{test_prompt}'")
            response = manager.generate_response(test_prompt)
            print(f"R2 Response: {response}")
            
            # Test proper unloading
            print("Testing model unloading...")
            unload_success = manager.unload_current_model()
            if unload_success:
                print("✓ Model unloaded successfully")
                
                # Force cleanup
                cleanup_success = manager.force_cleanup()
                if cleanup_success:
                    print("✓ Force cleanup completed")
                
                # Check memory after cleanup
                memory_final = manager.get_memory_usage()
                print(f"Memory after cleanup: {memory_final.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
            else:
                print("⚠ Model unload failed")
            
        else:
            print("⚠ Could not load Phi-3 model (this is expected if model files aren't downloaded)")
            print("This is normal for initial setup - the model will be downloaded on first use")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing model manager: {e}")
        return False


def test_translator():
    """Test the R2 translator functionality."""
    print("\n=== Testing R2 Translator ===")
    
    try:
        # Initialize translator (will work even without loaded model)
        translator = R2Translator()
        print("✓ R2 translator initialized")
        
        # Test human-to-R2 translation
        test_phrases = [
            "Hello R2, nice to meet you!",
            "Can you help me fix this droid?",
            "I'm feeling sad today",
            "That's amazing! Great job!",
            "I'm confused about this circuit",
            "Emergency! We need help now!"
        ]
        
        print("\nTesting human-to-R2 translation:")
        for phrase in test_phrases:
            r2_sound = translator.translate_to_r2(phrase)
            interpretation = translator.translate_from_r2(r2_sound)
            print(f"Human: '{phrase}'")
            print(f"R2: {r2_sound}")
            print(f"Meaning: {interpretation}")
            print()
        
        # Test conversation history
        history = translator.get_conversation_history()
        print(f"Conversation history entries: {len(history)}")
        
        # Test available emotions
        emotions = translator.get_available_emotions()
        print(f"Available emotions: {emotions}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing translator: {e}")
        return False


def test_integration():
    """Test the integrated AI system."""
    print("\n=== Testing Integrated System ===")
    
    try:
        # Create model manager and translator
        manager = ModelManager()
        translator = R2Translator(manager)
        
        print("✓ Integrated system initialized")
        
        # Test contextual responses
        test_conversations = [
            "Hi R2, what's your status?",
            "Can you run a diagnostic check?",
            "Thanks for your help!",
            "I need to find Princess Leia"
        ]
        
        print("\nTesting contextual conversations:")
        for message in test_conversations:
            r2_sounds, interpretation = translator.generate_contextual_response(message)
            print(f"You: {message}")
            print(f"R2: {r2_sounds}")
            print(f"Translation: {interpretation}")
            print()
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing integration: {e}")
        return False


def interactive_mode():
    """Run interactive chat with R2."""
    print("\n=== Interactive R2 Chat ===")
    print("Type 'quit' to exit, 'help' for commands")
    
    try:
        manager = ModelManager()
        translator = R2Translator(manager)
        
        # Try to load model (optional)
        print("Attempting to load AI model...")
        model_loaded = manager.load_model('phi-3')
        if model_loaded:
            print("✓ AI model loaded - responses will be AI-enhanced")
        else:
            print("⚠ Using rule-based responses (AI model not available)")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print("Commands:")
                    print("  help - Show this help")
                    print("  status - Show system status")
                    print("  history - Show conversation history")
                    print("  clear - Clear conversation history")
                    print("  quit/exit/q - Exit interactive mode")
                    continue
                elif user_input.lower() == 'status':
                    status = manager.get_model_status()
                    print(f"System status: {status}")
                    continue
                elif user_input.lower() == 'history':
                    history = translator.get_conversation_history()
                    for entry in history[-5:]:  # Show last 5
                        print(f"  {entry['speaker']}: {entry['message']}")
                    continue
                elif user_input.lower() == 'clear':
                    translator.clear_history()
                    print("Conversation history cleared")
                    continue
                elif not user_input:
                    continue
                
                # Generate R2 response
                r2_sounds, interpretation = translator.generate_contextual_response(user_input)
                print(f"R2: {r2_sounds}")
                print(f"(Translation: {interpretation})")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
    except Exception as e:
        print(f"Error in interactive mode: {e}")


def main():
    """Main test function."""
    print("R2 Astromech AI System Test")
    print("=" * 40)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_model_manager():
        tests_passed += 1
    
    if test_translator():
        tests_passed += 1
    
    if test_integration():
        tests_passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✓ All tests passed!")
        
        # Offer interactive mode
        try:
            choice = input("\nWould you like to try interactive mode? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                interactive_mode()
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        print("⚠ Some tests failed. Check the output above for details.")
    
    print("\nTest complete!")


if __name__ == '__main__':
    main()
