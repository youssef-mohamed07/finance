"""
Domain models for business logic
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    INCOME = "income"
    EXPENSE = "expense"


class Currency(str, Enum):
    """Supported currencies"""
    EGP = "EGP"
    USD = "USD"
    SAR = "SAR"
    EUR = "EUR"


class Category(BaseModel):
    """Transaction category"""
    
    name: str
    name_ar: str
    parent: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    keywords_ar: list[str] = Field(default_factory=list)


class Transaction(BaseModel):
    """Domain transaction model"""
    
    id: str
    amount: Optional[float] = None
    currency: Currency = Currency.EGP
    transaction_type: TransactionType
    category: str
    subcategory: Optional[str] = None
    item: Optional[str] = None
    merchant: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    extracted_from: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_response_model(self) -> dict:
        """Convert to API response format"""
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency.value,
            "category": self.category,
            "subcategory": self.subcategory,
            "item": self.item,
            "merchant": self.merchant,
            "location": self.location,
            "transaction_type": self.transaction_type.value,
            "confidence_score": self.confidence_score,
            "extracted_text": self.extracted_from
        }