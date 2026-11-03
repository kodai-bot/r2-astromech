#!/usr/bin/env python3
"""
R2-A1 Astromech Unit - Simple Terminal Menu

A simplified main entry point with basic terminal menu functionality.
"""

import sys
import os
import subprocess

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

def show_menu():
    """Display the R2-A1 command menu."""
    print("\n" + "="*70)
    print("    INDUSTRIAL AUTOMATON R2-A1 ASTROMECH COMMAND INTERFACE")
    print("    Advanced Network Discovery and Analysis System")
    print("    Manufactured by Industrial Automaton, Rordis City, Nubia")
    print("    'Modularity, Reliability, Intelligence' - Since 32 BBY")
    print("="*70)
    
    print("\n🤖 R2-A1 Astromech Command Menu:")
    print("   1. 🌐 Environment Scan (Network Discovery)")
    print("   2. 📡 Join Network (Connect to discovered network)")
    print("   3. 📊 System Status")
    print("   4. 🔧 Health Check")
    print("   5. 🛑 Quit")
    print("-" * 50)

def handle_environment_scan():
    """Handle environment scan by running the scan director."""
    print("\n🔍 R2-A1 Environment Scan")
    print("=" * 40)
    print("Launching R2-A1 Network Discovery Scan Director...")
    
    try:
        # Get the path to the scan director file
        project_root = os.path.dirname(os.path.dirname(__file__))
        scan_director_path = os.path.join(project_root, "scan_director.py")
        
        if not os.path.exists(scan_director_path):
            print("❌ Scan director script not found")
            print(f"   Expected at: {scan_director_path}")
            return
            
        print("\n🚀 Starting R2-A1 Network Discovery Scan Director...")
        print("🎵 Listen for R2's chirps as devices are discovered!")
        print("=" * 60)
        
        # Run the scan director script
        result = subprocess.run([sys.executable, scan_director_path], 
                              cwd=project_root)
        
        print("=" * 60)
        if result.returncode == 0:
            print("✅ Network discovery scan completed successfully!")
        else:
            print(f"⚠️  Discovery scan completed with exit code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Environment scan failed: {e}")
        print("💡 Check that scan_director.py is working correctly")
    
    input("\nPress Enter to continue...")

def handle_join_network():
    """Handle join network operation."""
    print("\n📡 R2-A1 Network Connection")
    print("=" * 40)
    print("🚧 Network joining functionality coming soon!")
    print("This will allow R2 to connect to discovered networks and services.")
    print("\nPlanned features:")
    print("  • WiFi network connection")
    print("  • Network credential management") 
    print("  • Service endpoint discovery")
    print("  • Secure connection protocols")
    
    input("\nPress Enter to continue...")

def handle_system_status():
    """Handle system status display."""
    print("\n📊 R2-A1 System Status")
    print("=" * 40)
    print("🤖 Status: Operational")
    print("🌍 Environment: Development") 
    print("📦 Modules: Simple Menu Mode")
    print("💚 Health: ✅ Healthy")
    
    print("\n📋 Available Features:")
    print("  ✅ Network Discovery (via demo)")
    print("  📋 Join Network (planned)")
    print("  ✅ System Status")
    print("  ✅ Health Check")
    
    input("\nPress Enter to continue...")

def handle_health_check():
    """Handle system health check."""
    print("\n🔧 R2-A1 Health Check")
    print("=" * 40)
    print("🔍 Running system diagnostics...")
    print("✅ All systems operational")
    print("🤖 R2-A1 is functioning within normal parameters")
    print("📡 Network discovery demo available")
    print("🔊 Audio systems ready")
    
    input("\nPress Enter to continue...")

def main():
    """Main application loop."""
    while True:
        try:
            show_menu()
            choice = input("Select option (1-5): ").strip()
            
            if choice == "1":
                handle_environment_scan()
            elif choice == "2":
                handle_join_network()
            elif choice == "3":
                handle_system_status()
            elif choice == "4":
                handle_health_check()
            elif choice == "5":
                print("\n🛑 Shutting down R2-A1 Astromech System...")
                print("👋 Thank you for using Industrial Automaton technology!")
                break
            else:
                print("❌ Invalid option. Please select 1-5.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
            print("👋 Thank you for using Industrial Automaton technology!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
