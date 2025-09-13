#!/usr/bin/env python3
"""
Jetson Nano Python 3.6.9 Compatibility Test
Tests our simplified R2 sound system on the Jetson Nano environment.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_python_version():
    """Test Python version compatibility."""
    print("🔍 Python Compatibility Test")
    print("=" * 40)
    print(f"Python version: {sys.version}")
    print(f"Version info: {sys.version_info}")
    
    # Check if we have at least Python 3.6
    if sys.version_info >= (3, 6):
        print("✅ Python version is compatible (3.6+)")
    else:
        print("❌ Python version too old (need 3.6+)")
        return False
    
    return True

def test_imports():
    """Test that all our imports work."""
    print("\n🔍 Import Test")
    print("=" * 40)
    
    try:
        # Test basic Python imports
        import typing
        from typing import Dict, List, Optional
        from pathlib import Path
        print("✅ Basic typing and pathlib imports work")
        
        # Test our simple sound system
        from personality.r2_simple_sounds import R2SimpleSounds, play_scanner_event
        print("✅ R2SimpleSounds import works")
        
        # Test network scanner
        from discovery.network_scanner import NetworkScanner
        print("✅ NetworkScanner import works")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without audio."""
    print("\n🔍 Basic Functionality Test")
    print("=" * 40)
    
    try:
        # Test creating simple sound engine (without initializing audio)
        from personality.r2_simple_sounds import R2SimpleSounds
        
        # Create instance but don't test audio (might not be available on headless system)
        engine = R2SimpleSounds()
        print("✅ R2SimpleSounds creation works")
        
        # Test vocabulary access
        vocab = engine.scanner_vocabulary
        print(f"✅ Vocabulary loaded: {len(vocab)} events")
        for event, letters in vocab.items():
            print(f"   {event} → '{letters}'")
        
        # Test network scanner creation
        from discovery.network_scanner import NetworkScanner
        scanner = NetworkScanner("127.0.0.1/32")
        print("✅ NetworkScanner creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_jetson_specific():
    """Test Jetson Nano specific features."""
    print("\n🔍 Jetson Nano Specific Test")
    print("=" * 40)
    
    # Check if we can detect we're on Jetson
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip()
            if 'Jetson' in model:
                print(f"✅ Running on Jetson: {model}")
            else:
                print(f"ℹ️  Not on Jetson (running on: {model})")
    except:
        print("ℹ️  Cannot detect hardware model")
    
    # Check available audio devices
    try:
        import subprocess
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Audio devices available:")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'card' in line.lower():
                    print(f"   {line}")
        else:
            print("⚠️  No audio devices found or aplay not available")
    except Exception as e:
        print(f"ℹ️  Audio device check failed: {e}")
    
    return True

def main():
    """Run all compatibility tests."""
    print("🤖 R2 Jetson Nano Compatibility Test")
    print("=" * 60)
    
    tests = [
        test_python_version,
        test_imports,
        test_basic_functionality,
        test_jetson_specific
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Code should work on Jetson Nano.")
    else:
        print("⚠️  Some tests failed. Check compatibility issues above.")

if __name__ == "__main__":
    main()
