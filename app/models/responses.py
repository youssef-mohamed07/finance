"""
Response models for API endpoints
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class APIResponse(BaseModel):
    """Base API response wrapper"""
    
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class SuccessResponse(APIResponse):
    """Success response wrapper"""
    
    data: Dict[str, Any]
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    """Error detail information"""
    
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(APIResponse):
    """Error response wrapper"""
    
    success: bool = False
    error: ErrorDetail


class TransactionDetail(BaseModel):
    """Individual transaction details"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: Optional[float] = Field(None, ge=0, description="Transaction amount")
    currency: str = Field(default="EGP", description="Currency code")
    category: str = Field(..., description="Transaction category")
    subcategory: Optional[str] = Field(None, description="Transaction subcategory")
    item: Optional[str] = Field(None, description="Item or service purchased")
    merchant: Optional[str] = Field(None, description="Merchant or place")
    location: Optional[str] = Field(None, description="Location of transaction")
    transaction_type: str = Field(..., description="income or expense")
    confidence_score: float = Field(default=0.8, ge=0, le=1, description="Confidence in extraction")
    extracted_text: Optional[str] = Field(None, description="Original text segment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 50.0,
                "currency": "EGP",
                "category": "طعام وشراب",
                "item": "خضار",
                "merchant": "كارفور",
                "transaction_type": "expense",
                "confidence_score": 0.9,
                "extracted_text": "دفعت 50 جنيه في كارفور على خضار"
            }
        }


class FinancialSummary(BaseModel):
    """Financial summary of all transactions"""
    
    total_transactions: int = Field(ge=0)
    total_income: float = Field(default=0, ge=0)
    total_expenses: float = Field(default=0, ge=0)
    net_amount: float = Field(default=0)
    currency: str = Field(default="EGP")
    categories: Dict[str, float] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_transactions": 2,
                "total_income": 0,
                "total_expenses": 75.0,
                "net_amount": -75.0,
                "currency": "EGP",
                "categories": {
                    "طعام وشراب": 50.0,
                    "مواصلات": 25.0
                }
            }
        }


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    
    transactions: List[TransactionDetail] = Field(default_factory=list)
    summary: FinancialSummary
    processing_time_ms: int = Field(ge=0)
    language_detected: str = Field(default="ar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transactions": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "amount": 50.0,
                        "currency": "EGP",
                        "category": "طعام وشراب",
                        "item": "خضار",
                        "merchant": "كارفور",
                        "transaction_type": "expense",
                        "confidence_score": 0.9
                    }
                ],
                "summary": {
                    "total_transactions": 1,
                    "total_expenses": 50.0,
                    "net_amount": -50.0,
                    "currency": "EGP"
                },
                "processing_time_ms": 150,
                "language_detected": "ar"
            }
        }


class TextAnalysisData(BaseModel):
    """Text analysis specific data"""
    
    original_text: str
    normalized_text: str
    analysis: AnalysisResult


class VoiceAnalysisData(BaseModel):
    """Voice analysis specific data"""
    
    transcription: str
    confidence_score: float = Field(ge=0, le=1)
    language_detected: str
    audio_duration_seconds: float = Field(ge=0)
    analysis: AnalysisResult


class TextAnalysisResponse(SuccessResponse):
    """Response for text analysis endpoint"""
    
    data: TextAnalysisData


class VoiceAnalysisResponse(SuccessResponse):
    """Response for voice analysis endpoint"""
    
    data: VoiceAnalysisData


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = "healthy"
    service: str = "finance-analyzer"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: Optional[float] = None