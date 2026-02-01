"""
Configuration settings for the Finance Analyzer application
"""
import os
from typing import Set, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = "Voice & Text Finance Analyzer"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080", 
        env="CORS_ORIGINS"
    )
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # External APIs
    assemblyai_api_key: str = Field(..., env="ASSEMBLYAI_API_KEY")
    api_timeout: int = Field(default=30, env="API_TIMEOUT")
    
    # Audio Processing
    sample_rate: int = 16000
    channels: int = 1
    
    # File Upload Limits
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_audio_extensions: Set[str] = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"}
    
    # Text Input Limits
    max_text_length: int = 1000
    min_text_length: int = 3
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=60, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: str = Field(default="1/minute", env="RATE_LIMIT_WINDOW")
    voice_rate_limit: str = Field(default="5/minute", env="VOICE_RATE_LIMIT")
    
    # Cache Configuration
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Database (for future use)
    database_url: str = Field(default="sqlite:///./finance_analyzer.db", env="DATABASE_URL")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Constants
CURRENCY_PATTERNS = [
    r'(\d+(?:[,.]?\d+)?)\s*(?:جنيه|جنية|جنيهات)',
    r'(\d+(?:[,.]?\d+)?)\s*(?:ريال|ريالات)',
    r'(\d+(?:[,.]?\d+)?)\s*(?:دولار|دولارات?)',
    r'(\d+(?:[,.]?\d+)?)\s*(?:pound|egp|sar|usd)',
]

INCOME_KEYWORDS = [
    'استلمت', 'مرتب', 'راتب', 'دخل', 'حصلت', 'قبضت', 'جالي', 'وصلني', 'جاني',
    'salary', 'income', 'received', 'earned', 'got', 'استلم', 'قبض', 'حولت لي',
    'وصل', 'حصل', 'كسبت', 'ربحت'
]

EXPENSE_KEYWORDS = [
    'دفعت', 'اشتريت', 'صرفت', 'خلصت', 'جبت', 'اخدت', 'شريت', 'اشتري',
    'paid', 'bought', 'spent', 'purchase', 'pay', 'دفع', 'شراء', 'حولت',
    'سددت', 'خلصت فلوس', 'كلت', 'شربت'
]