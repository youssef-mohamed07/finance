"""
File handling utilities
"""
import os
import tempfile
import secrets
from typing import Optional, Tuple
from contextlib import asynccontextmanager
from app.core.logging import get_logger
from app.core.security import SecurityUtils
from app.exceptions import FileValidationError

logger = get_logger("file_utils")


class SecureFileHandler:
    """Secure file handling with automatic cleanup"""
    
    def __init__(self):
        self.temp_files = set()
    
    @asynccontextmanager
    async def create_temp_file(self, content: bytes, original_filename: str):
        """Create a secure temporary file with automatic cleanup"""
        temp_path = None
        try:
            # Validate file content
            if not SecurityUtils.validate_audio_file_content(content, original_filename):
                raise FileValidationError(
                    f"Invalid audio file content: {original_filename}",
                    filename=original_filename
                )
            
            # Create secure temp directory
            temp_dir = tempfile.mkdtemp(prefix="finance_analyzer_")
            
            # Generate secure filename
            secure_filename = SecurityUtils.generate_secure_filename(original_filename)
            temp_path = os.path.join(temp_dir, secure_filename)
            
            # Write content securely
            with open(temp_path, 'wb') as f:
                f.write(content)
            
            # Set restrictive permissions
            os.chmod(temp_path, 0o600)
            
            self.temp_files.add(temp_path)
            logger.debug(f"Created secure temp file: {temp_path}")
            
            yield temp_path
            
        except Exception as e:
            logger.error(f"Error creating temp file: {e}")
            raise
        finally:
            # Cleanup
            if temp_path:
                await self.cleanup_file(temp_path)
    
    async def cleanup_file(self, file_path: str):
        """Securely cleanup a temporary file"""
        try:
            if os.path.exists(file_path):
                # Overwrite file content before deletion (security best practice)
                file_size = os.path.getsize(file_path)
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(file_size))
                
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
            
            # Remove from tracking
            self.temp_files.discard(file_path)
            
            # Try to remove parent directory if empty
            parent_dir = os.path.dirname(file_path)
            try:
                os.rmdir(parent_dir)
                logger.debug(f"Removed temp directory: {parent_dir}")
            except OSError:
                pass  # Directory not empty or other issue
                
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
    
    async def cleanup_all(self):
        """Cleanup all tracked temporary files"""
        for file_path in list(self.temp_files):
            await self.cleanup_file(file_path)


def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """Validate file extension"""
    if not filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions


def get_file_info(content: bytes, filename: str) -> dict:
    """Get file information"""
    return {
        "filename": filename,
        "size_bytes": len(content),
        "size_mb": round(len(content) / (1024 * 1024), 2),
        "extension": os.path.splitext(filename)[1].lower()
    }


# Global file handler instance
file_handler = SecureFileHandler()