"""
Content filtering utilities to prevent processing of illegal or harmful content
"""
import re
from typing import List, Tuple, Optional
from app.core.logging import get_logger
from app.exceptions import ValidationError

logger = get_logger("content_filter")


class ContentFilter:
    """Filter for detecting and blocking inappropriate content"""
    
    def __init__(self):
        # Illegal substances and activities (Arabic and English)
        self.illegal_substances = [
            # Arabic terms
            'حشيش', 'حشيشة', 'بانجو', 'ماريجوانا', 'كوكايين', 'هيروين', 'أفيون', 'ترامادول',
            'كبتاجون', 'إكستاسي', 'مخدرات', 'مخدر', 'مواد مخدرة', 'تجارة المخدرات',
            'بيع المخدرات', 'شراء المخدرات', 'تهريب المخدرات', 'مروج مخدرات',
            # English terms
            'drugs', 'cocaine', 'heroin', 'marijuana', 'cannabis', 'hashish', 'opium',
            'ecstasy', 'methamphetamine', 'drug dealing', 'drug trafficking', 'drug trade',
            'illegal drugs', 'narcotics', 'drug dealer', 'drug pusher'
        ]
        
        # Illegal activities
        self.illegal_activities = [
            # Arabic terms
            'غسيل أموال', 'غسيل الأموال', 'تبييض أموال', 'أموال مشبوهة', 'رشوة', 'فساد',
            'تهرب ضريبي', 'تجارة أسلحة', 'تهريب', 'احتيال', 'نصب', 'سرقة', 'اختلاس',
            'تزوير', 'تزييف', 'قتل', 'اغتيال', 'خطف', 'اتجار بالبشر', 'دعارة', 'بغاء',
            # English terms
            'money laundering', 'tax evasion', 'bribery', 'corruption', 'fraud', 'theft',
            'embezzlement', 'forgery', 'counterfeiting', 'murder', 'assassination',
            'kidnapping', 'human trafficking', 'prostitution', 'arms dealing', 'smuggling'
        ]
        
        # Weapons and explosives
        self.weapons_explosives = [
            # Arabic terms
            'أسلحة', 'سلاح', 'مسدس', 'بندقية', 'رشاش', 'قنابل', 'قنبلة', 'متفجرات',
            'ديناميت', 'تي إن تي', 'C4', 'أسلحة نارية', 'ذخيرة', 'رصاص',
            # English terms
            'weapons', 'gun', 'pistol', 'rifle', 'machine gun', 'bomb', 'explosive',
            'dynamite', 'TNT', 'ammunition', 'bullets', 'firearms', 'grenades'
        ]
        
        # Combine all prohibited terms
        self.prohibited_terms = (
            self.illegal_substances + 
            self.illegal_activities + 
            self.weapons_explosives
        )
        
        # Compile regex patterns for efficient matching
        self.prohibited_patterns = [
            re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            for term in self.prohibited_terms
        ]
    
    def check_content(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if content contains prohibited terms
        
        Returns:
            Tuple of (is_safe, list_of_found_terms)
        """
        if not text:
            return True, []
        
        found_terms = []
        text_lower = text.lower()
        
        for pattern in self.prohibited_patterns:
            matches = pattern.findall(text)
            if matches:
                found_terms.extend(matches)
        
        is_safe = len(found_terms) == 0
        
        if not is_safe:
            logger.warning(f"Prohibited content detected: {found_terms}")
        
        return is_safe, found_terms
    
    def filter_text(self, text: str) -> str:
        """
        Filter text by raising an exception if prohibited content is found
        
        Args:
            text: Text to check
            
        Returns:
            Original text if safe
            
        Raises:
            ValidationError: If prohibited content is detected
        """
        is_safe, found_terms = self.check_content(text)
        
        if not is_safe:
            raise ValidationError(
                "Content contains prohibited material and cannot be processed. "
                "This service is designed for legitimate financial transactions only.",
                details={
                    "reason": "prohibited_content",
                    "content_type": "illegal_or_harmful"
                }
            )
        
        return text
    
    def is_financial_content(self, text: str) -> bool:
        """
        Check if text appears to be legitimate financial content
        
        Args:
            text: Text to analyze
            
        Returns:
            True if content appears to be financial in nature
        """
        financial_indicators = [
            # Arabic financial terms
            'جنيه', 'دولار', 'ريال', 'دفعت', 'اشتريت', 'مرتب', 'راتب', 'فاتورة',
            'كارفور', 'سبينس', 'ميترو', 'مطعم', 'سوبر ماركت', 'صيدلية', 'بنزين',
            'مواصلات', 'تاكسي', 'قطار', 'مترو', 'كهرباء', 'مياه', 'انترنت',
            # English financial terms
            'pound', 'dollar', 'paid', 'bought', 'salary', 'bill', 'restaurant',
            'supermarket', 'pharmacy', 'gas', 'transport', 'taxi', 'electricity'
        ]
        
        text_lower = text.lower()
        financial_matches = sum(1 for term in financial_indicators if term in text_lower)
        
        # Consider it financial if it has at least 1 financial indicator
        return financial_matches > 0


# Global content filter instance
content_filter = ContentFilter()