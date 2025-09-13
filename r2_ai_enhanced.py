#!/usr/bin/env python3
"""
R2-D2 Astromech AI-Enhanced Control Program
==========================================

Enhanced version of R2's main control program with integrated AI capabilities
for intelligent network analysis, troubleshooting, and contextual insights.

Author: Dylan G Foley
Created: September 2025
Enhanced: AI Integration
Running on: NVIDIA Jetson Nano 4GB
"""

import sys
import os
import time
import logging
import argparse
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# R2 System Imports
from personality.r2_simple_sounds import init_simple_r2_audio, play_scanner_event
from discovery.network_scanner import NetworkScanner
from ai.network_analyzer import R2NetworkAnalyzer
from ai.model_manager import ModelManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class R2AstromechAIUnit:
    """
    R2-D2 Astromech Unit with AI Enhancement
    Coordinates all of R2's systems including AI-powered network analysis.
    """
    
    def __init__(self, audio_device=None, enable_ai=True):
        """Initialize R2's systems with AI capabilities."""
        self.audio_device = audio_device
        self.enable_ai = enable_ai
        self.audio_engine = None
        self.network_scanner = None
        self.ai_analyzer = None
        self.model_manager = None
        self.is_operational = False
        
        logger.info("🤖 R2-D2 AI-Enhanced Astromech Unit initializing...")
        
    def startup(self):
        """Startup sequence for R2 with AI capabilities."""
        print("=" * 70)
        print("🤖 R2-D2 AI-ENHANCED ASTROMECH UNIT - STARTUP SEQUENCE")
        print("=" * 70)
        
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
        
        # Initialize AI systems
        if self.enable_ai:
            try:
                logger.info("🧠 Initializing AI neural networks...")
                self.model_manager = ModelManager()
                self.ai_analyzer = R2NetworkAnalyzer(self.model_manager)
                logger.info("✅ R2 AI systems online")
                
                # Play AI activation sound
                if self.audio_engine and self.audio_engine.is_initialized:
                    # Use a sequence of sounds to indicate AI activation
                    time.sleep(0.5)
                    play_scanner_event('startup')  # Additional beep for AI
                    
            except Exception as e:
                logger.error(f"❌ AI system initialization failed: {e}")
                self.enable_ai = False
                logger.warning("⚠️  Continuing without AI enhancement")
        
        # Initialize network scanner
        try:
            logger.info("📡 Initializing network discovery systems...")
            self.network_scanner = NetworkScanner()
            logger.info("✅ Network scanner online")
            
        except Exception as e:
            logger.error(f"❌ Network scanner initialization failed: {e}")
            return False
        
        self.is_operational = True
        logger.info("🎉 R2-D2 AI-Enhanced Astromech Unit fully operational!")
        
        ai_status = "with AI enhancement" if self.enable_ai else "in basic mode"
        print(f"\n🤖 R2 is ready for operations {ai_status}!")
        return True
    
    def perform_network_scan(self, target_network=None, analyze_with_ai=True):
        """Perform a network discovery scan with optional AI analysis."""
        if not self.is_operational:
            logger.error("❌ R2 not operational - run startup() first")
            return []
            
        logger.info("🔍 R2 beginning network discovery mission...")
        
        if target_network:
            self.network_scanner.target_network = target_network
            logger.info(f"📡 Scanning custom network: {target_network}")
        else:
            logger.info(f"📡 Scanning network: {self.network_scanner.target_network}")
        
        # Perform the basic scan
        discovered_devices = self.network_scanner.scan_network()
        
        # Enhanced port scanning for active devices
        for device in discovered_devices:
            if device['status'] == 'active':
                logger.info(f"🔍 R2 analyzing device {device['ip']}...")
                port_info = self.network_scanner.port_scan(device['ip'])
                device['port_info'] = port_info
        
        # AI Analysis Phase
        ai_analysis = None
        if self.enable_ai and analyze_with_ai and self.ai_analyzer:
            try:
                logger.info("🧠 R2 AI systems analyzing discoveries...")
                ai_analysis = self.ai_analyzer.analyze_discovered_devices(discovered_devices)
                
                # Play R2 response sound
                if self.audio_engine and self.audio_engine.is_initialized:
                    # Convert R2 sound to audio event
                    self._play_r2_response(ai_analysis['r2_response'])
                
            except Exception as e:
                logger.error(f"❌ AI analysis failed: {e}")
        
        # Report Results
        self._report_scan_results(discovered_devices, ai_analysis)
        
        return discovered_devices, ai_analysis
    
    def diagnose_network_issue(self, device_ip: str, symptoms: str):
        """Use AI to diagnose a network issue."""
        if not self.enable_ai or not self.ai_analyzer:
            print("❌ AI diagnostics not available")
            return None
        
        # Gather device data
        device_data = f"IP: {device_ip}"
        if self.network_scanner:
            port_info = self.network_scanner.port_scan(device_ip)
            device_data += f", Open ports: {port_info.get('open_ports', [])}"
            device_data += f", Services: {list(port_info.get('services', {}).values())}"
        
        logger.info(f"🧠 R2 AI diagnosing issue with {device_ip}...")
        
        try:
            diagnosis = self.ai_analyzer.analyze_network_issue(device_data, symptoms)
            
            # Play R2 diagnostic response
            if self.audio_engine and self.audio_engine.is_initialized:
                self._play_r2_response(diagnosis['r2_response'])
            
            # Report diagnosis
            self._report_diagnosis(diagnosis)
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"❌ AI diagnosis failed: {e}")
            return None
    
    def security_assessment(self, devices=None):
        """Perform AI-powered security assessment."""
        if not self.enable_ai or not self.ai_analyzer:
            print("❌ AI security assessment not available")
            return None
        
        if not devices:
            # Perform fresh scan for security assessment
            logger.info("🔍 Performing security scan...")
            devices, _ = self.perform_network_scan(analyze_with_ai=False)
        
        logger.info("🔐 R2 AI analyzing network security posture...")
        
        try:
            security_report = self.ai_analyzer.assess_security_posture(devices)
            
            # Play R2 security response
            if self.audio_engine and self.audio_engine.is_initialized:
                self._play_r2_response(security_report['r2_response'])
            
            # Report security findings
            self._report_security_assessment(security_report)
            
            return security_report
            
        except Exception as e:
            logger.error(f"❌ Security assessment failed: {e}")
            return None
    
    def _play_r2_response(self, r2_sound: str):
        """Convert R2 sound description to audio playback."""
        # Map R2 sound characteristics to available sound events
        if 'urgent' in r2_sound or 'critical' in r2_sound:
            play_scanner_event('device_found')  # Urgent beeping
        elif 'error' in r2_sound or 'malfunction' in r2_sound:
            play_scanner_event('scan_complete')  # Error indication
        elif 'security' in r2_sound and 'alert' in r2_sound:
            play_scanner_event('device_found')  # Security alert
        else:
            play_scanner_event('scan_complete')  # Default response
    
    def _report_scan_results(self, devices, ai_analysis):
        """Report network scan results with AI insights."""
        print(f"\n🎯 R2 Discovery Mission Complete!")
        print(f"📊 Devices discovered: {len(devices)}")
        
        if devices:
            print("\n📡 Active Network Devices:")
            for device in devices:
                print(f"  • {device['ip']} - {device['status']} ({device['discovery_method']})")
                
                if device['status'] == 'active' and 'port_info' in device:
                    port_info = device['port_info']
                    if port_info['open_ports']:
                        print(f"    📡 Open ports: {port_info['open_ports']}")
                        services = list(port_info['services'].values())
                        if services:
                            print(f"    🛠️  Services: {', '.join(services)}")
                    else:
                        print(f"    🔒 No open ports detected")
        
        # AI Analysis Results
        if ai_analysis:
            print(f"\n🧠 R2 AI Analysis:")
            print(f"🤖 R2 says: {ai_analysis['r2_response']}")
            print(f"📋 Summary: {ai_analysis['summary']}")
            
            if ai_analysis.get('interesting_findings'):
                print(f"\n🔍 Key Findings:")
                for finding in ai_analysis['interesting_findings']:
                    print(f"  • {finding}")
            
            if ai_analysis.get('recommendations'):
                print(f"\n💡 R2 Recommendations:")
                for rec in ai_analysis['recommendations']:
                    print(f"  • {rec}")
            
            # Security assessment summary
            if ai_analysis.get('security_assessment'):
                security = ai_analysis['security_assessment']
                print(f"\n🔐 Security Status: {security.get('risk_level', 'UNKNOWN')}")
        else:
            print("\n⚠️  Basic scan mode (AI analysis not available)")
    
    def _report_diagnosis(self, diagnosis):
        """Report AI diagnosis results."""
        print(f"\n🧠 R2 AI Diagnostic Report:")
        print(f"🤖 R2 says: {diagnosis['r2_response']}")
        print(f"⚡ Urgency Level: {diagnosis['urgency_level']}")
        
        if 'diagnosis' in diagnosis:
            diag = diagnosis['diagnosis']
            
            if diag.get('likely_cause'):
                print(f"\n🔍 Most Likely Cause:")
                print(f"  {diag['likely_cause']}")
            
            if diag.get('diagnostic_steps'):
                print(f"\n📋 Diagnostic Steps:")
                for step in diag['diagnostic_steps']:
                    print(f"  • {step}")
            
            if diag.get('recommendations'):
                print(f"\n💡 Repair Recommendations:")
                for rec in diag['recommendations']:
                    print(f"  • {rec}")
            
            if diag.get('safety_considerations'):
                print(f"\n⚠️  Safety Considerations:")
                for safety in diag['safety_considerations']:
                    print(f"  • {safety}")
    
    def _report_security_assessment(self, security_report):
        """Report security assessment results."""
        print(f"\n🔐 R2 Security Assessment:")
        print(f"🤖 R2 says: {security_report['r2_response']}")
        print(f"⚡ Risk Level: {security_report['risk_level']}")
        print(f"📊 Devices Analyzed: {security_report['device_count']}")
        
        if security_report.get('security_concerns'):
            print(f"\n⚠️  Security Concerns:")
            for concern in security_report['security_concerns']:
                print(f"  • {concern}")
        else:
            print(f"\n✅ No significant security concerns detected")
        
        if security_report.get('recommendations'):
            print(f"\n💡 Security Recommendations:")
            for rec in security_report['recommendations']:
                print(f"  • {rec}")
    
    def interactive_mode(self):
        """Run R2 in interactive mode with AI commands."""
        print("\n🤖 R2-D2 AI-Enhanced Interactive Mode")
        print("=" * 50)
        print("Commands:")
        print("  'scan' or 's'        - Perform network scan with AI analysis")
        print("  'scan <network>'     - Scan specific network")
        print("  'security'           - Perform security assessment")
        print("  'diagnose'           - AI-powered network diagnostics")
        print("  'status'             - Show R2 system status")
        print("  'ai history'         - Show recent AI analysis history")
        print("  'help' or 'h'        - Show this help")
        print("  'quit' or 'q'        - Shutdown R2")
        print()
        
        while True:
            try:
                command = input("R2-AI > ").strip().lower()
                
                if command in ['quit', 'q', 'exit']:
                    break
                elif command in ['help', 'h']:
                    print("Available commands: scan, security, diagnose, status, ai history, help, quit")
                elif command == 'status':
                    self.show_status()
                elif command == 'security':
                    self.security_assessment()
                elif command == 'diagnose':
                    self._interactive_diagnose()
                elif command == 'ai history':
                    self._show_ai_history()
                elif command.startswith('scan'):
                    parts = command.split()
                    if len(parts) > 1:
                        target = parts[1]
                        self.perform_network_scan(target)
                    else:
                        self.perform_network_scan()
                elif command in ['scan', 's']:
                    self.perform_network_scan()
                elif command == '':
                    continue
                else:
                    print(f"🤖 R2 doesn't understand: '{command}'. Type 'help' for commands.")
                    
            except KeyboardInterrupt:
                print("\n🛑 R2 operation interrupted")
                break
            except Exception as e:
                logger.error(f"❌ Command error: {e}")
    
    def _interactive_diagnose(self):
        """Interactive diagnostic mode."""
        try:
            device_ip = input("Enter device IP to diagnose: ").strip()
            symptoms = input("Describe the symptoms: ").strip()
            
            if device_ip and symptoms:
                self.diagnose_network_issue(device_ip, symptoms)
            else:
                print("❌ Please provide both device IP and symptoms")
                
        except Exception as e:
            print(f"❌ Diagnostic error: {e}")
    
    def _show_ai_history(self):
        """Show recent AI analysis history."""
        if not self.enable_ai or not self.ai_analyzer:
            print("❌ AI not available")
            return
        
        history = self.ai_analyzer.get_analysis_history(5)
        
        if not history:
            print("📋 No AI analysis history available")
            return
        
        print(f"\n📋 Recent R2 AI Analysis History:")
        for i, analysis in enumerate(history[-5:], 1):
            timestamp = analysis.get('timestamp', 'Unknown time')
            summary = analysis.get('summary', 'No summary available')
            r2_response = analysis.get('r2_response', 'No R2 response')
            
            print(f"\n{i}. {timestamp}")
            print(f"   Summary: {summary}")
            print(f"   R2 said: {r2_response}")
    
    def show_status(self):
        """Show R2's current operational status including AI."""
        print("\n🤖 R2-D2 AI-Enhanced System Status:")
        print("-" * 40)
        print(f"Operational: {'✅ YES' if self.is_operational else '❌ NO'}")
        
        if self.audio_engine:
            audio_status = "✅ ONLINE" if self.audio_engine.is_initialized else "❌ OFFLINE"
            print(f"Audio System: {audio_status}")
            if self.audio_engine.is_initialized:
                print(f"Audio Device: {self.audio_engine.audio_device or 'default'}")
        else:
            print("Audio System: ❌ NOT INITIALIZED")
        
        # AI Status
        ai_status = "✅ ONLINE" if self.enable_ai and self.ai_analyzer else "❌ OFFLINE"
        print(f"AI Systems: {ai_status}")
        
        if self.enable_ai and self.model_manager:
            model_status = self.model_manager.get_model_status()
            if model_status['loaded']:
                model_info = model_status['model_info']
                print(f"AI Model: ✅ {model_info['name']} loaded")
                
                # Show memory usage if available
                try:
                    memory_info = self.model_manager.get_memory_usage()
                    sys_mem = memory_info.get('system_memory', {})
                    if 'rss_mb' in sys_mem:
                        print(f"Memory Usage: {sys_mem['rss_mb']:.1f}MB")
                except:
                    pass
            else:
                print(f"AI Model: ⚠️  Not loaded")
        
        if self.network_scanner:
            print(f"Network Scanner: ✅ ONLINE")
            print(f"Target Network: {self.network_scanner.target_network}")
        else:
            print("Network Scanner: ❌ NOT INITIALIZED")
        print()
    
    def shutdown(self):
        """Shutdown R2 systems including AI cleanup."""
        logger.info("🤖 R2-D2 AI-Enhanced Unit shutting down...")
        
        if self.audio_engine:
            try:
                play_scanner_event('shutdown')
                time.sleep(1)
                self.audio_engine.shutdown()
            except:
                pass
        
        # Cleanup AI systems
        if self.enable_ai and self.ai_analyzer:
            try:
                logger.info("🧠 Cleaning up AI systems...")
                self.ai_analyzer.cleanup()
            except:
                pass
        
        if self.model_manager:
            try:
                self.model_manager.force_cleanup()
            except:
                pass
        
        self.is_operational = False
        logger.info("👋 R2-D2 AI-Enhanced Unit offline")

def main():
    """Main entry point for R2-D2 AI-Enhanced Astromech Unit."""
    parser = argparse.ArgumentParser(description='R2-D2 AI-Enhanced Astromech Unit Control Program')
    parser.add_argument('--network', '-n', help='Target network to scan (e.g., 192.168.1.0/24)')
    parser.add_argument('--audio-device', '-a', help='Audio device to use (e.g., hw:3,0)')
    parser.add_argument('--scan-only', '-s', action='store_true', help='Perform single scan and exit')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI enhancement')
    parser.add_argument('--security-only', action='store_true', help='Perform security assessment only')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimize output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Initialize R2
    r2 = R2AstromechAIUnit(
        audio_device=args.audio_device,
        enable_ai=not args.no_ai
    )
    
    try:
        # Startup sequence
        if not r2.startup():
            logger.error("❌ R2 startup failed")
            return 1
        
        if args.scan_only:
            # Single scan mode
            r2.perform_network_scan(args.network)
        elif args.security_only:
            # Security assessment only
            r2.security_assessment()
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
