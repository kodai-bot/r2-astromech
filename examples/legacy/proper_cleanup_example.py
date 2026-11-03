#!/usr/bin/env python3
"""
Proper AI Model Cleanup Example

Demonstrates the correct way to load, use, and unload AI models
to avoid memory leaks and stuck GPU memory.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.ai.model_manager import ModelManager


def example_with_context_manager():
    """Example using context manager for automatic cleanup."""
    print("=== Example 1: Using Context Manager (Recommended) ===")
    
    # Using 'with' statement ensures automatic cleanup
    with ModelManager() as manager:
        print("📊 Initial memory usage:")
        memory_info = manager.get_memory_usage()
        print(f"   System: {memory_info.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
        
        print("\n🤖 Loading model...")
        success = manager.load_model('phi-3')
        
        if success:
            print("✓ Model loaded")
            
            # Check memory after loading
            memory_after = manager.get_memory_usage()
            print(f"📊 Memory after loading: {memory_after.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
            
            # Use the model
            response = manager.generate_response("Hello R2!")
            print(f"🤖 R2 says: {response}")
            
        else:
            print("⚠ Model not loaded (downloading on first use)")
    
    # When exiting the 'with' block, cleanup happens automatically
    print("✓ Context manager cleanup completed")


def example_with_manual_cleanup():
    """Example with manual cleanup control."""
    print("\n=== Example 2: Manual Cleanup Control ===")
    
    manager = None
    try:
        manager = ModelManager()
        
        print("📊 Initial memory:")
        memory_info = manager.get_memory_usage()
        print(f"   System: {memory_info.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
        
        print("\n🤖 Loading model...")
        success = manager.load_model('phi-3')
        
        if success:
            print("✓ Model loaded")
            
            memory_after = manager.get_memory_usage()
            print(f"📊 Memory after loading: {memory_after.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
            
            # Show GPU memory if available
            if memory_after.get('gpu_memory'):
                for device, gpu_info in memory_after['gpu_memory'].items():
                    if isinstance(gpu_info, dict) and 'allocated_gb' in gpu_info:
                        print(f"   GPU {device}: {gpu_info['allocated_gb']:.2f}GB")
            
            # Use the model
            response = manager.generate_response("Help me fix this droid!")
            print(f"🤖 R2 says: {response}")
            
            # Manual unload
            print("\n🧹 Manually unloading model...")
            unload_success = manager.unload_current_model()
            print(f"   Unload success: {unload_success}")
            
            # Force cleanup
            print("🧹 Force cleanup...")
            cleanup_success = manager.force_cleanup()
            print(f"   Cleanup success: {cleanup_success}")
            
            # Check final memory
            memory_final = manager.get_memory_usage()
            print(f"📊 Final memory: {memory_final.get('system_memory', {}).get('rss_mb', 'N/A'):.1f}MB")
            
        else:
            print("⚠ Model not loaded")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        # Ensure cleanup even if there's an error
        if manager is not None:
            print("🧹 Final cleanup in finally block...")
            manager.force_cleanup()


def example_memory_monitoring():
    """Example showing memory monitoring capabilities."""
    print("\n=== Example 3: Memory Monitoring ===")
    
    manager = ModelManager()
    
    def show_memory_status(label):
        memory_info = manager.get_memory_usage()
        print(f"\n📊 {label}:")
        
        # System memory
        sys_mem = memory_info.get('system_memory', {})
        if 'rss_mb' in sys_mem:
            print(f"   System: {sys_mem['rss_mb']:.1f}MB ({sys_mem.get('percent', 0):.1f}%)")
        
        # GPU memory
        gpu_mem = memory_info.get('gpu_memory', {})
        if gpu_mem and not gpu_mem.get('error'):
            for device, info in gpu_mem.items():
                if isinstance(info, dict):
                    print(f"   {device.upper()}: {info['allocated_gb']:.2f}GB / {info['total_gb']:.2f}GB "
                          f"({info['utilization_percent']:.1f}%)")
        elif gpu_mem.get('error'):
            print(f"   GPU: {gpu_mem['error']}")
        else:
            print("   GPU: No CUDA devices available")
    
    show_memory_status("Before loading")
    
    # Load model
    print("\n🤖 Loading model for memory monitoring...")
    if manager.load_model('phi-3'):
        show_memory_status("After loading")
        
        # Generate a few responses
        for i in range(3):
            response = manager.generate_response(f"Test message {i+1}")
            print(f"   Response {i+1}: {response[:50]}...")
        
        show_memory_status("After generation")
        
        # Unload
        manager.unload_current_model()
        show_memory_status("After unloading")
        
        # Force cleanup
        manager.force_cleanup()
        show_memory_status("After force cleanup")
    
    else:
        print("⚠ Could not load model for monitoring")


def main():
    """Run all cleanup examples."""
    print("R2 AI Model Cleanup Examples")
    print("=" * 50)
    
    try:
        # Example 1: Context manager (recommended)
        example_with_context_manager()
        
        # Example 2: Manual cleanup
        example_with_manual_cleanup()
        
        # Example 3: Memory monitoring
        example_memory_monitoring()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed!")
        print("\n💡 Key takeaways:")
        print("   1. Use 'with ModelManager() as manager:' for automatic cleanup")
        print("   2. Call manager.force_cleanup() for manual cleanup")
        print("   3. Monitor memory usage with manager.get_memory_usage()")
        print("   4. Always unload models before script termination")
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error in examples: {e}")


if __name__ == '__main__':
    main()
