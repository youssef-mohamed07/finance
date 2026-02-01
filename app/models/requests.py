"""
Request models for API endpoints
"""
from pydantic import BaseModel, Field, field_validator
from app.config import settings


class TextInput(BaseModel):
    """Input model for text analysis"""
    
    text: str = Field(
        ..., 
        min_length=settings.min_text_length, 
        max_length=settings.max_text_length,
        description="Text to analyze for financial information"
    )
    language: str = Field(default="ar", description="Language code (ar, en)")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        
        # Basic sanitization
        sanitized = v.strip()
        
        # Remove control characters except newlines and tabs
        sanitized = ''.join(
            char for char in sanitized 
            if ord(char) >= 32 or char in '\n\t'
        )
        
        return sanitized
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed_languages = {'ar', 'en', 'auto'}
        if v not in allowed_languages:
            raise ValueError(f'Language must be one of: {allowed_languages}')
        return v