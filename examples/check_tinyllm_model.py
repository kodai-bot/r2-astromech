#!/usr/bin/env python3
"""
Test TinyLLM Model Loading

This script tests the weiser/82M-0.4 model loading to ensure it works
correctly before integrating with the full R2 system.
"""

import asyncio
import sys
import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Add src to path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_model_loading():
    """Test loading the weiser/82M-0.4 model"""
    try:
        print("🧠 Testing TinyLLM Model Loading")
        print("=" * 50)
        
        model_path = "weiser/82M-0.4"
        print(f"📦 Model: {model_path}")
        print("💾 Device: CPU")
        print("🔧 Parameters: 82M")
        
        # Test 1: Load tokenizer
        print("\n🔤 Step 1: Loading Tokenizer")
        print("-" * 30)
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # Add padding token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        print("✅ Tokenizer loaded successfully")
        print(f"   Vocabulary size: {tokenizer.vocab_size}")
        print(f"   Model max length: {tokenizer.model_max_length}")
        
        # Test 2: Load model
        print("\n🤖 Step 2: Loading Model")
        print("-" * 30)
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        
        print("✅ Model loaded successfully")
        print(f"   Model type: {type(model).__name__}")
        print(f"   Device: {next(model.parameters()).device}")
        
        # Test 3: Basic generation
        print("\n💬 Step 3: Testing Generation")
        print("-" * 30)
        
        test_prompts = [
            "Hello, I am R2-D2.",
            "I found IoT devices on the network.",
            "Security analysis shows"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\nTest {i}: '{prompt}'")
            
            # Tokenize input
            inputs = tokenizer.encode(prompt, return_tensors="pt")
            print(f"   Input tokens: {inputs.shape}")
            
            # Generate response
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 20,  # Generate 20 more tokens
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"   Response: {response}")
        
        # Test 4: Memory usage
        print("\n💾 Step 4: Memory Usage")
        print("-" * 30)
        
        if torch.cuda.is_available():
            print("   CUDA available: Yes")
            print(f"   CUDA memory allocated: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
            print(f"   CUDA memory reserved: {torch.cuda.memory_reserved() / 1024**2:.1f} MB")
        else:
            print("   CUDA available: No")
        
        # Test 5: Cleanup
        print("\n🧹 Step 5: Cleanup")
        print("-" * 30)
        
        del model
        del tokenizer
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("✅ Model and tokenizer cleaned up successfully")
        
        print("\n🎉 All tests passed!")
        print("✅ The weiser/82M-0.4 model is ready for R2 integration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Model loading test failed: {e}")
        return False


async def test_r2_integration():
    """Test R2 integration with the model"""
    try:
        print("\n🤖 Testing R2 Integration")
        print("=" * 50)
        
        from src.modules.ai.models.tinyllm_model import TinyLLMModel
        
        # Create model with test configuration
        config = {
            'model_path': 'weiser/82M-0.4',
            'device': 'cpu',
            'max_length': 128,
            'temperature': 0.7,
            'iot_mode': True,
            'enable_quantization': False  # Disable for testing
        }
        
        model = TinyLLMModel(config)
        
        # Test model loading
        print("Loading TinyLLM model...")
        success = await model.load_model()
        
        if success:
            print("✅ TinyLLM model loaded successfully")
            
            # Test model info
            model_info = await model.get_model_info()
            print("\n📋 Model Information:")
            print(f"   Name: {model_info['name']}")
            print(f"   Type: {model_info['type']}")
            print(f"   Parameters: {model_info['parameters']}")
            print(f"   Device: {model_info['device']}")
            print(f"   Optimization: {model_info['optimization']}")
            
            # Test generation
            print("\n💬 Testing Generation:")
            test_input = "Hello R2! How are you today?"
            response = await model.generate_response(test_input)
            print(f"   Input: {test_input}")
            print(f"   Response: {response}")
            
            # Test R2 sound translation
            r2_sounds = await model.translate_to_r2(test_input)
            print(f"   R2 Sounds: {r2_sounds}")
            
            # Test IoT analysis
            print("\n🔬 Testing IoT Analysis:")
            iot_input = "I found temperature sensors DS18B20 and MQTT broker on port 1883"
            iot_response = await model.generate_response(iot_input)
            print(f"   Input: {iot_input}")
            print(f"   Response: {iot_response}")
            
            # Cleanup
            await model.unload_model()
            print("\n✅ R2 integration test completed successfully")
            
        else:
            print("❌ Failed to load TinyLLM model")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ R2 integration test failed: {e}")
        logger.error(f"R2 integration test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🧪 TinyLLM Model Test Suite")
    print("=" * 60)
    print("This test suite verifies the weiser/82M-0.4 model works correctly")
    print("before integrating with the full R2 system.")
    print("=" * 60)
    
    try:
        # Test 1: Basic model loading
        print("\n🔬 Test 1: Basic Model Loading")
        success1 = await test_model_loading()
        
        if not success1:
            print("\n❌ Basic model loading failed - stopping tests")
            return 1
        
        # Test 2: R2 integration
        print("\n🤖 Test 2: R2 Integration")
        success2 = await test_r2_integration()
        
        if success1 and success2:
            print("\n🎉 All tests passed!")
            print("✅ The weiser/82M-0.4 model is ready for production use")
            print("🚀 You can now run the full R2 demos with TinyLLM")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        logger.error(f"Test suite error: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)