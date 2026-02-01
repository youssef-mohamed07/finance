"""
NLP service for text analysis and transaction extraction
"""
import re
import time
import uuid
from typing import List, Dict, Any, Optional
from app.core.logging import get_logger
from app.utils.text_utils import (
    normalize_arabic_text, extract_amounts_from_text, 
    split_text_into_segments, detect_language
)
from app.utils.cache import cached_text_analysis
from app.utils.content_filter import content_filter
from app.models.domain import Transaction, TransactionType
from app.models.responses import TransactionDetail, FinancialSummary, AnalysisResult
from app.config import INCOME_KEYWORDS, EXPENSE_KEYWORDS
from app.exceptions import NLPProcessingError, ValidationError

logger = get_logger("nlp_service")


class CategoryClassifier:
    """Classify transactions into categories"""
    
    def __init__(self):
        self.category_map = {
            'طعام وشراب': {
                'keywords': [
                    'طعام', 'أكل', 'اكل', 'خضار', 'خضروات', 'فواكه', 'فاكهة', 'لحم', 'لحمة', 
                    'فراخ', 'فرخة', 'دجاج', 'سمك', 'عيش', 'خبز', 'جبنة', 'جبن', 'لبن', 'حليب',
                    'بيض', 'زيت', 'سكر', 'رز', 'أرز', 'مكرونة', 'معكرونة', 'بطاطس',
                    'مطعم', 'restaurant', 'كشري', 'فول', 'طعمية', 'قهوة', 'كافيه', 'كافي',
                    'food', 'grocery', 'vegetables', 'fruits', 'meat', 'chicken', 'fish'
                ],
                'places': ['كارفور', 'carrefour', 'سبينس', 'spinneys', 'ميترو', 'metro']
            },
            'مواصلات': {
                'keywords': [
                    'مواصلات', 'بنزين', 'وقود', 'سولار', 'تاكسي', 'أوبر', 'اوبر', 'كريم', 'مترو', 
                    'اتوبيس', 'ميكروباص', 'توكتوك', 'اجرة', 'عربية', 'سيارة', 'قطر', 'قطار',
                    'تذكرة', 'تسكرة', 'ركبت', 'transport', 'gas', 'fuel', 'taxi', 'uber', 'careem', 
                    'bus', 'metro', 'car', 'train', 'ticket'
                ],
                'places': []
            },
            'تسوق': {
                'keywords': [
                    'محل', 'سوبر ماركت', 'supermarket', 'بقالة', 'بقال', 'جمعية', 'حاجات',
                    'تسوق', 'shopping', 'mall', 'مول'
                ],
                'places': ['كارفور', 'carrefour', 'سبينس', 'spinneys', 'ميترو', 'metro']
            },
            'مرتب ودخل': {
                'keywords': [
                    'مرتب', 'راتب', 'معاش', 'salary', 'wage', 'قبضت', 'استلمت مرتب', 
                    'مكافأة', 'بونص', 'حافز', 'عمولة', 'ارباح', 'دخل'
                ],
                'places': []
            },
            'ملابس': {
                'keywords': [
                    'ملابس', 'هدوم', 'لبس', 'جزمة', 'شنطة', 'حذاء', 'بنطلون', 'قميص',
                    'فستان', 'جاكت', 'بلوفر', 'جينز', 'عطر', 'مكياج', 'اكسسوار',
                    'clothes', 'shopping', 'shoes', 'bag'
                ],
                'places': ['مول', 'سيتي ستارز', 'مول العرب']
            },
            'فواتير': {
                'keywords': [
                    'فاتورة', 'كهرباء', 'كهربا', 'مياه', 'ميه', 'انترنت', 'نت', 'موبايل', 
                    'تليفون', 'غاز', 'تلفون', 'خط', 'باقة', 'اشتراك',
                    'bill', 'electricity', 'water', 'internet', 'mobile', 'phone', 'gas', 'subscription'
                ],
                'places': []
            },
            'ترفيه': {
                'keywords': [
                    'سينما', 'فيلم', 'ترفيه', 'مسرح', 'حفلة', 'حفل', 'كونسرت', 'نادي', 'جيم',
                    'cinema', 'movie', 'entertainment', 'film', 'concert', 'gym', 'club'
                ],
                'places': []
            },
            'صحة': {
                'keywords': [
                    'دواء', 'طبيب', 'صيدلية', 'دكتور', 'علاج', 'مستشفى', 'عيادة', 'تحليل', 
                    'اشعة', 'كشف', 'عملية', 'روشتة',
                    'medicine', 'doctor', 'pharmacy', 'health', 'hospital', 'clinic', 'medical'
                ],
                'places': []
            }
        }
    
    def classify(self, text: str, place: Optional[str] = None) -> str:
        """Classify transaction into category"""
        text_lower = normalize_arabic_text(text.lower())
        
        # Special cases first
        if 'تذكرة' in text_lower or 'تسكرة' in text_lower:
            return 'مواصلات'
        
        if 'قهوة' in text_lower or 'كافيه' in text_lower:
            return 'طعام وشراب'
        
        # Check place-based classification
        if place:
            place_lower = place.lower()
            for category, data in self.category_map.items():
                if any(p in place_lower for p in data['places']):
                    return category
        
        # Check keyword-based classification
        for category, data in self.category_map.items():
            if any(keyword in text_lower for keyword in data['keywords']):
                return category
        
        return 'أخرى'


class TransactionExtractor:
    """Extract transaction details from text segments"""
    
    def __init__(self):
        self.classifier = CategoryClassifier()
        self.places_map = {
            'كارفور': ['كارفور', 'carrefour'],
            'سبينس': ['سبينس', 'spinneys'],
            'ميترو': ['metro', 'ميترو'],
            'خير زمان': ['خير زمان'],
            'العثيم': ['العثيم'],
            'بنده': ['بنده', 'panda'],
            'هايبر': ['هايبر', 'hyper'],
            'لولو': ['لولو', 'lulu'],
            'فتح الله': ['فتح الله', 'fathalla'],
            'كازيون': ['كازيون', 'kazyon'],
            'سيتي ستارز': ['سيتي ستارز', 'city stars'],
            'مول العرب': ['مول العرب', 'mall of arabia'],
        }
    
    def extract_place(self, text: str) -> Optional[str]:
        """Extract place/merchant from text"""
        text_lower = text.lower()
        
        for place_name, keywords in self.places_map.items():
            if any(kw in text_lower for kw in keywords):
                return place_name
        
        return None
    
    def extract_item(self, text: str, category: str) -> Optional[str]:
        """Extract item from text based on category"""
        text_lower = text.lower()
        
        # Special cases
        if 'قهوة' in text_lower:
            return 'قهوة'
        elif 'تذكرة' in text_lower or 'تسكرة' in text_lower:
            return 'تذكرة'
        elif 'حاجات' in text_lower:
            return 'حاجات متنوعة'
        
        # Pattern-based extraction
        item_patterns = [
            r'(?:على|علي)\s+(\w+)',           # على خضار
            r'(?:من|في)\s+(\w+)',              # من اللحم
            r'(?:اشتريت|شريت|جبت|اخدت)\s+(\w+)',  # اشتريت خضار
        ]
        
        for pattern in item_patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_item = match.group(1)
                # Filter out common words and places
                excluded = ['في', 'من', 'على', 'ال', 'the', 'a', 'an', 'كارفور', 'ميترو', 
                           'حاجة', 'جوه', 'للقطر', 'قطر', 'قطار']
                if potential_item not in excluded:
                    return potential_item
        
        return None
    
    def determine_transaction_type(self, text: str) -> TransactionType:
        """Determine if transaction is income or expense"""
        text_lower = text.lower()
        
        is_income = any(keyword in text_lower for keyword in INCOME_KEYWORDS)
        return TransactionType.INCOME if is_income else TransactionType.EXPENSE
    
    def extract_transaction(self, text: str, amount: Optional[float] = None) -> Transaction:
        """Extract complete transaction from text segment"""
        # If no amount provided, try to extract it
        if amount is None:
            amounts = extract_amounts_from_text(text)
            amount = amounts[0][0] if amounts else None
        
        # Extract components
        place = self.extract_place(text)
        transaction_type = self.determine_transaction_type(text)
        category = self.classifier.classify(text, place)
        item = self.extract_item(text, category)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(text, amount, place, item)
        
        return Transaction(
            id=str(uuid.uuid4()),
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            item=item,
            merchant=place,
            confidence_score=confidence,
            extracted_from=text
        )
    
    def _calculate_confidence(self, text: str, amount: Optional[float], 
                            place: Optional[str], item: Optional[str]) -> float:
        """Calculate confidence score for extraction"""
        score = 0.5  # Base score
        
        # Amount found
        if amount is not None:
            score += 0.3
        
        # Place found
        if place:
            score += 0.1
        
        # Item found
        if item:
            score += 0.1
        
        # Contains action verbs
        action_verbs = ['دفعت', 'اشتريت', 'جبت', 'استلمت', 'قبضت']
        if any(verb in text.lower() for verb in action_verbs):
            score += 0.1
        
        return min(score, 1.0)


class NLPService:
    """Main NLP service for financial text analysis"""
    
    def __init__(self):
        self.extractor = TransactionExtractor()
    
    @cached_text_analysis(ttl=3600)  # Cache for 1 hour
    async def analyze_text(self, text: str, language: str = "ar") -> AnalysisResult:
        """Analyze text and extract financial information"""
        start_time = time.time()
        
        try:
            logger.info(f"Analyzing text: {text[:50]}...")
            
            # CRITICAL: Filter content for prohibited material
            content_filter.filter_text(text)
            
            # Additional check: Ensure content is financial in nature
            if not content_filter.is_financial_content(text):
                raise ValidationError(
                    "Content does not appear to be financial in nature. "
                    "This service is designed for legitimate financial transaction analysis only.",
                    details={
                        "reason": "non_financial_content",
                        "content_type": "non_financial"
                    }
                )
            
            # Normalize text
            normalized_text = normalize_arabic_text(text)
            
            # Detect language if auto
            if language == "auto":
                language = detect_language(text)
            
            # Extract all amounts
            all_amounts = extract_amounts_from_text(text)
            logger.debug(f"Found {len(all_amounts)} amounts: {[a[0] for a in all_amounts]}")
            
            # Split into segments
            segments = split_text_into_segments(text)
            logger.debug(f"Split into {len(segments)} segments")
            
            # Extract transactions
            transactions = []
            used_amounts = set()
            
            for segment in segments:
                # Filter each segment as well
                try:
                    content_filter.filter_text(segment)
                except ValidationError:
                    logger.warning(f"Skipping prohibited segment: {segment[:30]}...")
                    continue
                
                # Skip segments that don't represent transactions
                if not self._is_transaction_segment(segment):
                    continue
                
                # Find amount for this segment
                segment_amounts = extract_amounts_from_text(segment)
                amount = None
                
                if segment_amounts:
                    amount = segment_amounts[0][0]
                    used_amounts.add(amount)
                else:
                    # Assign unused amount if this looks like a spending action
                    if self._indicates_spending(segment):
                        for amt, pos in all_amounts:
                            if amt not in used_amounts:
                                amount = amt
                                used_amounts.add(amt)
                                break
                
                # Extract transaction
                transaction = self.extractor.extract_transaction(segment, amount)
                
                # Only include meaningful transactions
                if self._is_meaningful_transaction(transaction):
                    transactions.append(transaction)
            
            # If no valid transactions found after filtering, return empty result
            if not transactions:
                logger.info("No valid financial transactions found after content filtering")
                return AnalysisResult(
                    transactions=[],
                    summary=FinancialSummary(
                        total_transactions=0,
                        total_income=0,
                        total_expenses=0,
                        net_amount=0,
                        categories={}
                    ),
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    language_detected=language
                )
            
            # Calculate summary
            summary = self._calculate_summary(transactions)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Convert to response format
            transaction_details = [
                TransactionDetail(**transaction.to_response_model())
                for transaction in transactions
            ]
            
            result = AnalysisResult(
                transactions=transaction_details,
                summary=summary,
                processing_time_ms=processing_time,
                language_detected=language
            )
            
            logger.info(f"Analysis completed: {len(transactions)} transactions, {processing_time}ms")
            return result
            
        except ValidationError:
            # Re-raise validation errors (including content filtering)
            raise
        except Exception as e:
            logger.error(f"NLP analysis failed: {e}", exc_info=True)
            raise NLPProcessingError(f"Failed to analyze text: {str(e)}")
    
    def _is_transaction_segment(self, segment: str) -> bool:
        """Check if segment represents a transaction"""
        segment_lower = segment.lower()
        
        # Must contain action verbs or amounts
        action_verbs = ['دفعت', 'اشتريت', 'جبت', 'استلمت', 'قبضت', 'صرفت', 'كلت', 'شربت']
        has_action = any(verb in segment_lower for verb in action_verbs)
        has_amount = bool(extract_amounts_from_text(segment))
        
        return has_action or has_amount
    
    def _indicates_spending(self, segment: str) -> bool:
        """Check if segment indicates spending"""
        spending_verbs = ['دفعت', 'اشتريت', 'جبت', 'صرفت', 'كلت', 'شربت', 'خلصت']
        return any(verb in segment.lower() for verb in spending_verbs)
    
    def _is_meaningful_transaction(self, transaction: Transaction) -> bool:
        """Check if transaction is meaningful enough to include"""
        # Must have amount or clear merchant/item
        has_amount = transaction.amount is not None
        has_context = transaction.merchant or transaction.item
        
        # Must not be just movement without spending
        return has_amount or has_context
    
    def _calculate_summary(self, transactions: List[Transaction]) -> FinancialSummary:
        """Calculate financial summary"""
        total_income = sum(
            t.amount for t in transactions 
            if t.transaction_type == TransactionType.INCOME and t.amount
        )
        
        total_expenses = sum(
            t.amount for t in transactions 
            if t.transaction_type == TransactionType.EXPENSE and t.amount
        )
        
        # Calculate categories
        categories = {}
        for transaction in transactions:
            if transaction.amount and transaction.category:
                categories[transaction.category] = categories.get(transaction.category, 0) + transaction.amount
        
        return FinancialSummary(
            total_transactions=len(transactions),
            total_income=total_income,
            total_expenses=total_expenses,
            net_amount=total_income - total_expenses,
            categories=categories
        )