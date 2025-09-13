"""
Custom Exceptions for R2 Astromech System

This module defines custom exceptions used throughout the R2 system.
"""


class R2Exception(Exception):
    """Base exception for R2 system"""
    pass


class R2ModuleException(R2Exception):
    """Exception raised by modules"""
    
    def __init__(self, module_name: str, message: str, original_exception: Exception = None):
        self.module_name = module_name
        self.original_exception = original_exception
        super().__init__(f"[{module_name}] {message}")


class R2ConfigurationException(R2Exception):
    """Exception raised for configuration errors"""
    pass


class R2ServiceException(R2Exception):
    """Exception raised by services"""
    
    def __init__(self, service_name: str, message: str, original_exception: Exception = None):
        self.service_name = service_name
        self.original_exception = original_exception
        super().__init__(f"[{service_name}] {message}")


class R2NetworkException(R2Exception):
    """Exception raised for network-related errors"""
    pass


class R2AIException(R2Exception):
    """Exception raised for AI-related errors"""
    pass


class R2AudioException(R2Exception):
    """Exception raised for audio-related errors"""
    pass


class R2OperationException(R2Exception):
    """Exception raised for operation errors"""
    
    def __init__(self, operation_id: str, message: str, original_exception: Exception = None):
        self.operation_id = operation_id
        self.original_exception = original_exception
        super().__init__(f"[Operation {operation_id}] {message}")


class R2TimeoutException(R2Exception):
    """Exception raised for timeout errors"""
    pass


class R2ValidationException(R2Exception):
    """Exception raised for validation errors"""
    pass


class R2ResourceException(R2Exception):
    """Exception raised for resource-related errors"""
    pass