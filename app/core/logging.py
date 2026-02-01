"""
Logging configuration and utilities
"""
import logging
import sys
from datetime import datetime
from typing import Dict, Any
import json
from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Setup application logging"""
    
    # Create logger
    logger = logging.getLogger("finance_analyzer")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.debug:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # JSON format for production
        formatter = JSONFormatter()
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(f"finance_analyzer.{name}")


def log_request(logger: logging.Logger, method: str, path: str, 
                client_ip: str, duration_ms: float, status_code: int):
    """Log HTTP request"""
    logger.info(
        "HTTP request completed",
        extra={
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "type": "http_request"
        }
    )


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log error with context"""
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "type": "error"
        },
        exc_info=True
    )