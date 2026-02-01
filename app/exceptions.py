"""
Custom exceptions for the Finance Analyzer application
"""
from typing import Optional, Dict, Any


class FinanceAnalyzerError(Exception):
    """Base exception for Finance Analyzer"""
    
    def __init__(self, message: str, code: str = "GENERIC_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(FinanceAnalyzerError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class AudioProcessingError(FinanceAnalyzerError):
    """Raised when audio processing fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUDIO_PROCESSING_ERROR", details)


class TranscriptionError(FinanceAnalyzerError):
    """Raised when transcription fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TRANSCRIPTION_ERROR", details)


class FileValidationError(FinanceAnalyzerError):
    """Raised when file validation fails"""
    
    def __init__(self, message: str, filename: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FILE_VALIDATION_ERROR", details)
        self.filename = filename


class NLPProcessingError(FinanceAnalyzerError):
    """Raised when NLP processing fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NLP_PROCESSING_ERROR", details)


class RateLimitError(FinanceAnalyzerError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)