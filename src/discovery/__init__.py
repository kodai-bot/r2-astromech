"""
R2 Astromech Project - Discovery Module
Running on: NVIDIA Jetson Nano 4GB
Purpose: Universal device discovery and communication
Author: [Dylan Foley]
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .network_scanner import NetworkScanner
from .protocol_detector import ProtocolDetector

__all__ = ['NetworkScanner', 'ProtocolDetector']
