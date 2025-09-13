#!/usr/bin/env python3
"""
AI Model Cleanup Utility

Force unload AI models and clear GPU memory.
Useful for when models are stuck in memory after script termination.
"""

import gc
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def force_cleanup():
    """Force cleanup of AI models and GPU memory."""
    print("🧹 Starting AI model cleanup...")
    
    # Force garbage collection
    print("   Collecting garbage...")
    collected = gc.collect()
    print(f"   Collected {collected} objects")
    
    if HAS_TORCH:
        # Clear PyTorch cache
        print("   Clearing PyTorch cache...")
        
        if torch.cuda.is_available():
            # Clear CUDA cache
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            # Get memory info
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3   # GB
            
            print(f"   GPU Memory - Allocated: {memory_allocated:.2f}GB, Reserved: {memory_reserved:.2f}GB")
            
            if memory_allocated > 0.1:  # If more than 100MB still allocated
                print("   ⚠️  Warning: GPU memory still allocated after cleanup")
                print("   You may need to restart Python to fully free GPU memory")
            else:
                print("   ✓ GPU memory cleaned successfully")
        else:
            print("   No CUDA devices available")
        
        # Clear CPU tensors
        if hasattr(torch, '_C') and hasattr(torch._C, '_cuda_clearCublasWorkspaces'):
            torch._C._cuda_clearCublasWorkspaces()
    else:
        print("   PyTorch not available, skipping tensor cleanup")
    
    # Additional cleanup
    print("   Running additional cleanup...")
    for _ in range(3):
        gc.collect()
    
    print("✓ Cleanup complete!")

def check_memory_usage():
    """Check current memory usage."""
    print("📊 Memory Usage Status:")
    
    if HAS_TORCH and torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            device = f"cuda:{i}"
            allocated = torch.cuda.memory_allocated(device) / 1024**3
            reserved = torch.cuda.memory_reserved(device) / 1024**3
            total = torch.cuda.get_device_properties(device).total_memory / 1024**3
            
            print(f"   GPU {i}: {allocated:.2f}GB / {total:.2f}GB allocated ({allocated/total*100:.1f}%)")
            print(f"           {reserved:.2f}GB reserved")
    else:
        print("   No CUDA devices available for memory check")

def main():
    """Main cleanup function."""
    print("R2 AI Model Cleanup Utility")
    print("=" * 40)
    
    try:
        check_memory_usage()
        print()
        force_cleanup()
        print()
        check_memory_usage()
        
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == '__main__':
    main()
