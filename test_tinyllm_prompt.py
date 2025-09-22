#!/usr/bin/env python3
"""
Test TinyLLM Prompt System

Quick test to see how TinyLLM responds to our network diagnostic prompts
and optimize the system prompt for better results.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("❌ Transformers not available")
    exit(1)

class TinyLLMTester:
    """Simple TinyLLM tester for prompt optimization."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
    
    async def initialize(self):
        """Initialize TinyLLM."""
        try:
            print("🔄 Loading TinyLLM...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                "weiser/82M-0.4",
                trust_remote_code=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                "weiser/82M-0.4",
                trust_remote_code=True,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            
            self.is_loaded = True
            print("✅ TinyLLM loaded")
            return True
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            return False
    
    async def test_prompt(self, prompt: str, system_prompt: str = "") -> str:
        """Test a prompt with optional system context."""
        if not self.is_loaded:
            return "Model not loaded"
        
        try:
            full_prompt = system_prompt + prompt if system_prompt else prompt
            
            print(f"\n📝 Testing prompt:")
            print(f"   Input: {full_prompt[:100]}...")
            
            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=60,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    max_length=inputs['input_ids'].shape[1] + 20,  # Short response
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.8,
                    top_k=40,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            ).strip()
            
            print(f"   Output: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Generation error: {e}"
            print(f"   Error: {error_msg}")
            return error_msg

async def main():
    """Test different prompt strategies."""
    print("🤖 TinyLLM Prompt Testing")
    print("=" * 50)
    
    tester = TinyLLMTester()
    
    if not await tester.initialize():
        return 1
    
    # Test cases
    test_cases = [
        {
            "name": "Direct Question",
            "prompt": "Device has hostname 'router' and ports [22, 80]. What type?",
            "system": ""
        },
        {
            "name": "With System Prompt v1",
            "prompt": "Device has hostname 'router' and ports [22, 80]. What type?",
            "system": "You are a network diagnostic assistant. Reply with device type only. "
        },
        {
            "name": "With System Prompt v2", 
            "prompt": "Device has hostname 'router' and ports [22, 80]. What type?",
            "system": "Network analysis: answer briefly. "
        },
        {
            "name": "Simple Format",
            "prompt": "router hostname, ports 22,80 = ",
            "system": ""
        },
        {
            "name": "Classification Format",
            "prompt": "classify: hostname=router ports=22,80",
            "system": "device types: router, computer, printer, iot_sensor, camera. classify: "
        }
    ]
    
    print(f"\n🧪 Running {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        
        response = await tester.test_prompt(
            test_case['prompt'], 
            test_case['system']
        )
        
        # Wait a bit between tests
        await asyncio.sleep(0.5)
    
    print(f"\n✅ Testing complete")
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))
