"""
Monitoring Module Interfaces

This module defines the interfaces for monitoring functionality
including health monitoring, metrics collection, and alerting.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime

from ...core.interfaces import IModule


class IHealthMonitor(IModule):
    """Health Monitoring interface"""
    
    @abstractmethod
    async def check_system_health(self) -> Dict[str, Any]:
        """
        Check overall system health.
        
        Returns:
            Dict[str, Any]: System health status
        """
        pass
    
    @abstractmethod
    async def check_module_health(self, module_name: str) -> Dict[str, Any]:
        """
        Check health of specific module.
        
        Args:
            module_name: Name of module to check
            
        Returns:
            Dict[str, Any]: Module health status
        """
        pass
    
    @abstractmethod
    async def check_resource_usage(self) -> Dict[str, Any]:
        """
        Check system resource usage.
        
        Returns:
            Dict[str, Any]: Resource usage information
        """
        pass
    
    @abstractmethod
    async def check_network_health(self) -> Dict[str, Any]:
        """
        Check network connectivity and health.
        
        Returns:
            Dict[str, Any]: Network health status
        """
        pass
    
    @abstractmethod
    async def get_health_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get health check history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Health check history
        """
        pass


class IMetricsCollector(IModule):
    """Metrics Collection interface"""
    
    @abstractmethod
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collect system-level metrics.
        
        Returns:
            Dict[str, Any]: System metrics
        """
        pass
    
    @abstractmethod
    async def collect_module_metrics(self, module_name: str) -> Dict[str, Any]:
        """
        Collect metrics for specific module.
        
        Args:
            module_name: Name of module
            
        Returns:
            Dict[str, Any]: Module metrics
        """
        pass
    
    @abstractmethod
    async def collect_network_metrics(self) -> Dict[str, Any]:
        """
        Collect network-related metrics.
        
        Returns:
            Dict[str, Any]: Network metrics
        """
        pass
    
    @abstractmethod
    async def collect_ai_metrics(self) -> Dict[str, Any]:
        """
        Collect AI-related metrics.
        
        Returns:
            Dict[str, Any]: AI metrics
        """
        pass
    
    @abstractmethod
    async def collect_audio_metrics(self) -> Dict[str, Any]:
        """
        Collect audio-related metrics.
        
        Returns:
            Dict[str, Any]: Audio metrics
        """
        pass
    
    @abstractmethod
    async def get_metrics_summary(self, time_range: str = "1h") -> Dict[str, Any]:
        """
        Get metrics summary for time range.
        
        Args:
            time_range: Time range (1h, 24h, 7d)
            
        Returns:
            Dict[str, Any]: Metrics summary
        """
        pass


class IAlertManager(IModule):
    """Alert Management interface"""
    
    @abstractmethod
    async def create_alert(self, alert_type: str, severity: str, message: str, 
                          data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new alert.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity (low, medium, high, critical)
            message: Alert message
            data: Additional alert data
            
        Returns:
            str: Alert ID
        """
        pass
    
    @abstractmethod
    async def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve alert.
        
        Args:
            alert_id: Alert identifier
            
        Returns:
            bool: True if resolved successfully
        """
        pass
    
    @abstractmethod
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get active alerts.
        
        Returns:
            List[Dict[str, Any]]: Active alerts
        """
        pass
    
    @abstractmethod
    async def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List[Dict[str, Any]]: Alert history
        """
        pass
    
    @abstractmethod
    async def set_alert_threshold(self, metric: str, threshold: float, 
                                severity: str = "medium") -> bool:
        """
        Set alert threshold for metric.
        
        Args:
            metric: Metric name
            threshold: Threshold value
            severity: Alert severity when threshold exceeded
            
        Returns:
            bool: True if threshold set successfully
        """
        pass
    
    @abstractmethod
    async def check_thresholds(self, metrics: Dict[str, float]) -> List[str]:
        """
        Check metrics against thresholds.
        
        Args:
            metrics: Current metric values
            
        Returns:
            List[str]: List of triggered alert IDs
        """
        pass


class IPerformanceMonitor(IModule):
    """Performance Monitoring interface"""
    
    @abstractmethod
    async def measure_operation_time(self, operation_name: str) -> Callable:
        """
        Create timer context for operation.
        
        Args:
            operation_name: Name of operation to measure
            
        Returns:
            Callable: Context manager for timing
        """
        pass
    
    @abstractmethod
    async def record_operation_metrics(self, operation_name: str, duration: float, 
                                     success: bool, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record operation performance metrics.
        
        Args:
            operation_name: Name of operation
            duration: Operation duration in seconds
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        pass
    
    @abstractmethod
    async def get_performance_summary(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Args:
            operation_name: Specific operation name, or None for all
            
        Returns:
            Dict[str, Any]: Performance summary
        """
        pass
    
    @abstractmethod
    async def get_slow_operations(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """
        Get operations slower than threshold.
        
        Args:
            threshold: Duration threshold in seconds
            
        Returns:
            List[Dict[str, Any]]: Slow operations
        """
        pass


class IResourceMonitor(IModule):
    """Resource Monitoring interface"""
    
    @abstractmethod
    async def get_cpu_usage(self) -> float:
        """
        Get CPU usage percentage.
        
        Returns:
            float: CPU usage percentage
        """
        pass
    
    @abstractmethod
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage information.
        
        Returns:
            Dict[str, Any]: Memory usage details
        """
        pass
    
    @abstractmethod
    async def get_disk_usage(self) -> Dict[str, Any]:
        """
        Get disk usage information.
        
        Returns:
            Dict[str, Any]: Disk usage details
        """
        pass
    
    @abstractmethod
    async def get_network_usage(self) -> Dict[str, Any]:
        """
        Get network usage information.
        
        Returns:
            Dict[str, Any]: Network usage details
        """
        pass
    
    @abstractmethod
    async def get_gpu_usage(self) -> Dict[str, Any]:
        """
        Get GPU usage information.
        
        Returns:
            Dict[str, Any]: GPU usage details
        """
        pass
    
    @abstractmethod
    async def get_process_info(self) -> Dict[str, Any]:
        """
        Get process information.
        
        Returns:
            Dict[str, Any]: Process details
        """
        pass


class ILogAnalyzer(IModule):
    """Log Analysis interface"""
    
    @abstractmethod
    async def analyze_log_errors(self, time_range: str = "1h") -> List[Dict[str, Any]]:
        """
        Analyze error logs.
        
        Args:
            time_range: Time range to analyze
            
        Returns:
            List[Dict[str, Any]]: Error analysis results
        """
        pass
    
    @abstractmethod
    async def get_log_statistics(self, time_range: str = "1h") -> Dict[str, Any]:
        """
        Get log statistics.
        
        Args:
            time_range: Time range to analyze
            
        Returns:
            Dict[str, Any]: Log statistics
        """
        pass
    
    @abstractmethod
    async def search_logs(self, query: str, time_range: str = "1h") -> List[Dict[str, Any]]:
        """
        Search logs for specific patterns.
        
        Args:
            query: Search query
            time_range: Time range to search
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        pass
    
    @abstractmethod
    async def get_log_trends(self, metric: str, time_range: str = "24h") -> List[Dict[str, Any]]:
        """
        Get log trends for specific metric.
        
        Args:
            metric: Metric to analyze
            time_range: Time range for trend analysis
            
        Returns:
            List[Dict[str, Any]]: Trend data
        """
        pass