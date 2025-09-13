#!/usr/bin/env python3
"""
R2-D2 Astromech Main Control Program
====================================

This is R2's main control program that initializes all systems and 
coordinates network scanning operations.

Author: Dylan G Foley
Created: September 2025
Running on: NVIDIA Jetson Nano 4GB
"""

import sys
import os
import time
import logging
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# R2 System Imports
from personality.r2_simple_sounds import init_simple_r2_audio, play_scanner_event
from discovery.network_scanner import NetworkScanner

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class R2AstromechUnit:
    """
    R2-D2 Astromech Unit Main Controller
    Coordinates all of R2's systems and operations.
    """
    
    def __init__(self, audio_device=None):
        """Initialize R2's systems."""
        self.audio_device = audio_device
        self.audio_engine = None
        self.network_scanner = None
        self.is_operational = False
        
        logger.info("🤖 R2-D2 Astromech Unit initializing...")
        
    def startup(self):
        """Startup sequence for R2."""
        print("=" * 60)
        print("🤖 R2-D2 ASTROMECH UNIT - STARTUP SEQUENCE")
        print("=" * 60)
        
        # Initialize audio personality system
        try:
            logger.info("🔊 Initializing R2 audio personality system...")
            self.audio_engine = init_simple_r2_audio(audio_device=self.audio_device)
            
            if self.audio_engine and self.audio_engine.is_initialized:
                logger.info("✅ R2 audio system online")
                play_scanner_event('startup')  # R2 says hello!
            else:
                logger.warning("⚠️  R2 audio system offline (silent mode)")
                
        except Exception as e:
            logger.error(f"❌ Audio system initialization failed: {e}")
        
        # Initialize network scanner
        try:
            logger.info("📡 Initializing network discovery systems...")
            # Default to local network, but can be overridden
            self.network_scanner = NetworkScanner()
            logger.info("✅ Network scanner online")
            
        except Exception as e:
            logger.error(f"❌ Network scanner initialization failed: {e}")
            return False
        
        self.is_operational = True
        logger.info("🎉 R2-D2 Astromech Unit fully operational!")
        print("\n🤖 R2 is ready for operations!")
        return True
    
    def perform_network_scan(self, target_network=None):
        """Perform a network discovery scan."""
        if not self.is_operational:
            logger.error("❌ R2 not operational - run startup() first")
            return []
            
        logger.info("🔍 R2 beginning network discovery mission...")
        
        if target_network:
            # Update scanner target if specified
            self.network_scanner.target_network = target_network
            logger.info(f"📡 Scanning custom network: {target_network}")
        else:
            logger.info(f"📡 Scanning network: {self.network_scanner.target_network}")
        
        # Perform the scan
        discovered_devices = self.network_scanner.scan_network()
        
        # Report results
        print(f"\n🎯 R2 Discovery Mission Complete!")
        print(f"📊 Devices discovered: {len(discovered_devices)}")
        
        if discovered_devices:
            print("\n📡 Active Network Devices:")
            for device in discovered_devices:
                print(f"  • {device['ip']} - {device['status']} ({device['discovery_method']})")
                
                # Optional: Scan ports on discovered devices
                if device['status'] == 'active':
                    print(f"    🔍 R2 analyzing device {device['ip']}...")
                    port_info = self.network_scanner.port_scan(device['ip'])
                    
                    if port_info['open_ports']:
                        print(f"    📡 Open ports: {port_info['open_ports']}")
                        services = list(port_info['services'].values())
                        if services:
                            print(f"    🛠️  Services: {', '.join(services)}")
                    else:
                        print(f"    🔒 No open ports detected")
        else:
            print("🤔 No active devices found in target network")
        
        return discovered_devices
    
    def interactive_mode(self):
        """Run R2 in interactive mode."""
        print("\n🤖 R2-D2 Interactive Mode")
        print("=" * 40)
        print("Commands:")
        print("  'scan' or 's'     - Perform network scan")
        print("  'scan <network>'  - Scan specific network (e.g., '192.168.1.0/24')")
        print("  'status'          - Show R2 status")
        print("  'help' or 'h'     - Show this help")
        print("  'quit' or 'q'     - Shutdown R2")
        print()
        
        while True:
            try:
                command = input("R2-D2 > ").strip().lower()
                
                if command in ['quit', 'q', 'exit']:
                    break
                elif command in ['help', 'h']:
                    print("Available commands: scan, status, help, quit")
                elif command == 'status':
                    self.show_status()
                elif command.startswith('scan'):
                    parts = command.split()
                    if len(parts) > 1:
                        # Custom network specified
                        target = parts[1]
                        self.perform_network_scan(target)
                    else:
                        # Default network scan
                        self.perform_network_scan()
                elif command in ['scan', 's']:
                    self.perform_network_scan()
                elif command == '':
                    continue  # Empty input
                else:
                    print(f"🤖 R2 doesn't understand: '{command}'. Type 'help' for commands.")
                    
            except KeyboardInterrupt:
                print("\n🛑 R2 operation interrupted")
                break
            except Exception as e:
                logger.error(f"❌ Command error: {e}")
    
    def show_status(self):
        """Show R2's current operational status."""
        print("\n🤖 R2-D2 System Status:")
        print("-" * 30)
        print(f"Operational: {'✅ YES' if self.is_operational else '❌ NO'}")
        
        if self.audio_engine:
            audio_status = "✅ ONLINE" if self.audio_engine.is_initialized else "❌ OFFLINE"
            print(f"Audio System: {audio_status}")
            if self.audio_engine.is_initialized:
                print(f"Audio Device: {self.audio_engine.audio_device or 'default'}")
        else:
            print("Audio System: ❌ NOT INITIALIZED")
            
        if self.network_scanner:
            print(f"Network Scanner: ✅ ONLINE")
            print(f"Target Network: {self.network_scanner.target_network}")
        else:
            print("Network Scanner: ❌ NOT INITIALIZED")
        print()
    
    def shutdown(self):
        """Shutdown R2 systems."""
        logger.info("🤖 R2-D2 shutting down...")
        
        if self.audio_engine:
            try:
                play_scanner_event('shutdown')  # R2 says goodbye (using startup sound for now)
                time.sleep(1)  # Give time for goodbye sound
                self.audio_engine.shutdown()
            except:
                pass
        
        self.is_operational = False
        logger.info("👋 R2-D2 offline")

def main():
    """Main entry point for R2-D2 Astromech Unit."""
    parser = argparse.ArgumentParser(description='R2-D2 Astromech Unit Control Program')
    parser.add_argument('--network', '-n', help='Target network to scan (e.g., 192.168.1.0/24)')
    parser.add_argument('--audio-device', '-a', help='Audio device to use (e.g., hw:3,0)')
    parser.add_argument('--scan-only', '-s', action='store_true', help='Perform single scan and exit')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimize output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Initialize R2
    r2 = R2AstromechUnit(audio_device=args.audio_device)
    
    try:
        # Startup sequence
        if not r2.startup():
            logger.error("❌ R2 startup failed")
            return 1
        
        if args.scan_only:
            # Single scan mode
            r2.perform_network_scan(args.network)
        else:
            # Interactive mode
            if args.network:
                # Perform initial scan of specified network
                r2.perform_network_scan(args.network)
            
            # Enter interactive mode
            r2.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n🛑 R2 operation interrupted by user")
    except Exception as e:
        logger.error(f"❌ R2 operation failed: {e}")
    finally:
        # Shutdown sequence
        r2.shutdown()
    
    return 0

if __name__ == "__main__":
    exit(main())
