"""
Service Layer Interfaces

This module defines the interfaces for the service layer,
which orchestrates operations across multiple modules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from ..core.interfaces import IModule


class OperationStatus(Enum):
    """Operation status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationType(Enum):
    """Operation type enumeration"""
    NETWORK_SCAN = "network_scan"
    DEVICE_ANALYSIS = "device_analysis"
    AI_ANALYSIS = "ai_analysis"
    SECURITY_ASSESSMENT = "security_assessment"
    AUDIO_PLAYBACK = "audio_playback"
    SYSTEM_DIAGNOSTIC = "system_diagnostic"


@dataclass
class Operation:
    """Operation information"""
    id: str
    type: OperationType
    status: OperationStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: Dict[str, Any] = None
    results: Dict[str, Any] = None
    error_message: Optional[str] = None
    progress: float = 0.0


class IOrchestrationService(IModule):
    """Main orchestration service interface"""
    
    @abstractmethod
    async def start_operation(self, operation_type: OperationType, 
                            parameters: Dict[str, Any]) -> str:
        """
        Start a new operation.
        
        Args:
            operation_type: Type of operation to start
            parameters: Operation parameters
            
        Returns:
            str: Operation ID
        """
        pass
    
    @abstractmethod
    async def get_operation_status(self, operation_id: str) -> Optional[Operation]:
        """
        Get operation status.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Optional[Operation]: Operation information
        """
        pass
    
    @abstractmethod
    async def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel running operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            bool: True if cancelled successfully
        """
        pass
    
    @abstractmethod
    async def get_active_operations(self) -> List[Operation]:
        """
        Get list of active operations.
        
        Returns:
            List[Operation]: Active operations
        """
        pass
    
    @abstractmethod
    async def get_operation_history(self, limit: int = 100) -> List[Operation]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List[Operation]: Operation history
        """
        pass
    
    @abstractmethod
    async def schedule_operation(self, operation_type: OperationType,
                               parameters: Dict[str, Any], 
                               schedule_time: datetime) -> str:
        """
        Schedule operation for future execution.
        
        Args:
            operation_type: Type of operation
            parameters: Operation parameters
            schedule_time: When to execute the operation
            
        Returns:
            str: Scheduled operation ID
        """
        pass


class INetworkService(IModule):
    """Network service interface"""
    
    @abstractmethod
    async def discover_devices(self, target_network: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover network devices.
        
        Args:
            target_network: Target network (e.g., '192.168.1.0/24')
            
        Returns:
            List[Dict[str, Any]]: Discovered devices
        """
        pass
    
    @abstractmethod
    async def analyze_device(self, device_ip: str) -> Dict[str, Any]:
        """
        Analyze specific device.
        
        Args:
            device_ip: Device IP address
            
        Returns:
            Dict[str, Any]: Device analysis results
        """
        pass
    
    @abstractmethod
    async def scan_device_ports(self, device_ip: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Scan ports on device.
        
        Args:
            device_ip: Device IP address
            ports: List of ports to scan
            
        Returns:
            Dict[str, Any]: Port scan results
        """
        pass
    
    @abstractmethod
    async def perform_security_assessment(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform security assessment of devices.
        
        Args:
            devices: List of devices to assess
            
        Returns:
            Dict[str, Any]: Security assessment results
        """
        pass
    
    @abstractmethod
    async def monitor_network_health(self, target_hosts: List[str]) -> Dict[str, Any]:
        """
        Monitor network health.
        
        Args:
            target_hosts: List of hosts to monitor
            
        Returns:
            Dict[str, Any]: Network health status
        """
        pass


class IAIService(IModule):
    """AI service interface"""
    
    @abstractmethod
    async def analyze_network_data(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze network data using AI.
        
        Args:
            devices: Network device data
            
        Returns:
            Dict[str, Any]: AI analysis results
        """
        pass
    
    @abstractmethod
    async def diagnose_network_issue(self, device_ip: str, symptoms: str) -> Dict[str, Any]:
        """
        Diagnose network issue using AI.
        
        Args:
            device_ip: Device IP address
            symptoms: Issue symptoms
            
        Returns:
            Dict[str, Any]: Diagnosis results
        """
        pass
    
    @abstractmethod
    async def generate_r2_response(self, context: str, data: Dict[str, Any]) -> str:
        """
        Generate R2-style response.
        
        Args:
            context: Response context
            data: Context data
            
        Returns:
            str: R2 response
        """
        pass
    
    @abstractmethod
    async def translate_human_to_r2(self, text: str) -> str:
        """
        Translate human text to R2 sounds.
        
        Args:
            text: Human text
            
        Returns:
            str: R2 sound sequence
        """
        pass
    
    @abstractmethod
    async def translate_r2_to_human(self, r2_sounds: str) -> str:
        """
        Translate R2 sounds to human text.
        
        Args:
            r2_sounds: R2 sound sequence
            
        Returns:
            str: Human text
        """
        pass
    
    @abstractmethod
    async def get_ai_model_status(self) -> Dict[str, Any]:
        """
        Get AI model status.
        
        Returns:
            Dict[str, Any]: Model status information
        """
        pass


class IPersonalityService(IModule):
    """Personality service interface"""
    
    @abstractmethod
    async def express_emotion(self, emotion: str, context: str, intensity: float = 0.5) -> str:
        """
        Express emotion through audio.
        
        Args:
            emotion: Emotion to express
            context: Context for emotion
            intensity: Emotion intensity
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def respond_to_scan_results(self, devices_found: int, errors: int = 0) -> str:
        """
        Respond to network scan results.
        
        Args:
            devices_found: Number of devices found
            errors: Number of errors
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def respond_to_ai_analysis(self, analysis_type: str, results: Dict[str, Any]) -> str:
        """
        Respond to AI analysis results.
        
        Args:
            analysis_type: Type of analysis
            results: Analysis results
            
        Returns:
            str: Generated sound sequence
        """
        pass
    
    @abstractmethod
    async def play_sound_sequence(self, sequence: str, volume: float = 0.7) -> bool:
        """
        Play sound sequence.
        
        Args:
            sequence: Sound sequence to play
            volume: Volume level
            
        Returns:
            bool: True if played successfully
        """
        pass
    
    @abstractmethod
    async def set_personality_mode(self, mode: str) -> bool:
        """
        Set personality mode.
        
        Args:
            mode: Personality mode
            
        Returns:
            bool: True if mode set successfully
        """
        pass


class ISystemService(IModule):
    """System service interface"""
    
    @abstractmethod
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.
        
        Returns:
            Dict[str, Any]: System status
        """
        pass
    
    @abstractmethod
    async def get_module_status(self, module_name: str) -> Dict[str, Any]:
        """
        Get module status.
        
        Args:
            module_name: Name of module
            
        Returns:
            Dict[str, Any]: Module status
        """
        pass
    
    @abstractmethod
    async def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform system health check.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        pass
    
    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics.
        
        Returns:
            Dict[str, Any]: System metrics
        """
        pass
    
    @abstractmethod
    async def restart_module(self, module_name: str) -> bool:
        """
        Restart specific module.
        
        Args:
            module_name: Name of module to restart
            
        Returns:
            bool: True if restarted successfully
        """
        pass
    
    @abstractmethod
    async def shutdown_system(self) -> bool:
        """
        Shutdown the entire system.
        
        Returns:
            bool: True if shutdown successful
        """
        pass


class IWorkflowService(IModule):
    """Workflow service interface"""
    
    @abstractmethod
    async def create_workflow(self, name: str, steps: List[Dict[str, Any]]) -> str:
        """
        Create new workflow.
        
        Args:
            name: Workflow name
            steps: Workflow steps
            
        Returns:
            str: Workflow ID
        """
        pass
    
    @abstractmethod
    async def execute_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> str:
        """
        Execute workflow.
        
        Args:
            workflow_id: Workflow identifier
            parameters: Workflow parameters
            
        Returns:
            str: Execution ID
        """
        pass
    
    @abstractmethod
    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get workflow execution status.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            Dict[str, Any]: Execution status
        """
        pass
    
    @abstractmethod
    async def get_available_workflows(self) -> List[Dict[str, Any]]:
        """
        Get available workflows.
        
        Returns:
            List[Dict[str, Any]]: Available workflows
        """
        pass