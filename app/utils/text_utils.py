"""
Text processing utilities
"""
import re
from typing import List, Tuple
from app.core.logging import get_logger

logger = get_logger("text_utils")


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text for better processing"""
    if not text:
        return ""
    
    # Arabic-Indic digits
    arabic_indic = '٠١٢٣٤٥٦٧٨٩'
    # Extended Arabic-Indic (used in some regions)
    extended_arabic = '۰۱۲۳۴۵۶۷۸۹'
    english = '0123456789'
    
    # Convert both variants
    for arabic, eng in zip(arabic_indic + extended_arabic, english * 2):
        text = text.replace(arabic, eng)
    
    # Handle Arabic decimal separators
    text = text.replace('٫', '.').replace('،', ',')
    
    # Normalize Arabic characters
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    
    # Remove diacritics
    diacritics = 'ًٌٍَُِّْ'
    for diacritic in diacritics:
        text = text.replace(diacritic, '')
    
    return text


def extract_amounts_from_text(text: str) -> List[Tuple[float, int]]:
    """Extract all amounts from text with their positions"""
    original_text = text
    text = normalize_arabic_text(text)
    text_lower = text.lower()
    
    amounts = []  # List of (amount, position) tuples
    
    # Enhanced Arabic number words dictionary
    number_words = {
        # Units (1-9)
        'واحد': 1, 'واحدة': 1, 'اتنين': 2, 'اثنين': 2, 'اثنان': 2, 'تنين': 2,
        'ثلاثة': 3, 'تلاتة': 3, 'تلاته': 3, 'ثلاث': 3,
        'اربعة': 4, 'اربع': 4, 'أربعة': 4, 'أربع': 4, 'اربعه': 4,
        'خمسة': 5, 'خمس': 5, 'خمسه': 5,
        'ستة': 6, 'ست': 6, 'سته': 6,
        'سبعة': 7, 'سبع': 7, 'سبعه': 7,
        'ثمانية': 8, 'تمانية': 8, 'ثمان': 8, 'تمان': 8, 'تمانيه': 8,
        'تسعة': 9, 'تسع': 9, 'تسعه': 9,
        # Tens (10-90)
        'عشرة': 10, 'عشر': 10, 'عشره': 10,
        'عشرين': 20, 'عشرون': 20,
        'ثلاثين': 30, 'ثلاثون': 30, 'تلاتين': 30, 'تلاتون': 30,
        'اربعين': 40, 'اربعون': 40, 'أربعين': 40,
        'خمسين': 50, 'خمسون': 50,
        'ستين': 60, 'ستون': 60,
        'سبعين': 70, 'سبعون': 70,
        'ثمانين': 80, 'ثمانون': 80, 'تمانين': 80, 'تمانون': 80,
        'تسعين': 90, 'تسعون': 90,
        # Hundreds
        'مية': 100, 'ميه': 100, 'مائة': 100, 'مئة': 100, 'مائه': 100,
        'ميتين': 200, 'مئتين': 200, 'مائتين': 200, 'ميتان': 200,
        'تلتمية': 300, 'ثلثمائة': 300, 'تلاتمية': 300,
        'اربعمية': 400, 'أربعمائة': 400, 'اربعمائة': 400,
        'خمسمية': 500, 'خمسمائة': 500, 'خمسميه': 500,
        'ستمية': 600, 'ستمائة': 600,
        'سبعمية': 700, 'سبعمائة': 700,
        'تمنمية': 800, 'ثمانمائة': 800, 'تمانمية': 800,
        'تسعمية': 900, 'تسعمائة': 900,
        # Thousands
        'الف': 1000, 'ألف': 1000, 'الاف': 1000, 'آلاف': 1000,
        'الفين': 2000, 'ألفين': 2000, 'الفان': 2000, 'ألفان': 2000,
    }
    
    # Extract from Arabic word numbers
    words = text_lower.split()
    word_positions = []
    current_pos = 0
    
    for word in words:
        word_positions.append(current_pos)
        # Handle attached prepositions
        clean_word = word
        if word.startswith(('ب', 'ل', 'ك')):
            clean_word = word[1:]
        
        clean_word = re.sub(r'[^\w\s]', '', clean_word)
        
        if clean_word in number_words:
            amounts.append((number_words[clean_word], current_pos))
        
        current_pos += len(word) + 1
    
    # Extract digit patterns with enhanced currency detection
    from app.config import CURRENCY_PATTERNS
    
    for pattern in CURRENCY_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            try:
                amount_str = match.group(1).replace(',', '').replace('٫', '.').strip()
                if amount_str:
                    amount = float(amount_str)
                    if amount > 0:
                        amounts.append((amount, match.start()))
            except (ValueError, IndexError):
                continue
    
    # Also look for standalone numbers
    for match in re.finditer(r'(\d+(?:[,.]?\d+)?)', text_lower):
        try:
            amount_str = match.group(1).replace(',', '').strip()
            if amount_str:
                amount = float(amount_str)
                if amount > 0:
                    amounts.append((amount, match.start()))
        except ValueError:
            continue
    
    # Remove duplicates by position and sort
    unique_amounts = []
    seen_positions = set()
    
    for amount, pos in sorted(amounts, key=lambda x: x[1]):
        # Allow some tolerance for position matching
        position_key = pos // 5  # Group positions within 5 characters
        if position_key not in seen_positions:
            seen_positions.add(position_key)
            unique_amounts.append((amount, pos))
    
    logger.debug(f"Extracted {len(unique_amounts)} amounts: {[a[0] for a in unique_amounts]}")
    return unique_amounts


def split_text_into_segments(text: str) -> List[str]:
    """Split text into transaction segments"""
    # Enhanced splitting patterns
    patterns = [
        r'وبعدين\s*',  # وبعدين
        r'و\s*(?=جبت|رحت|ركبت|كلت|اشتريت|دفعت|شريت)',  # و before action verbs
        r'بعد\s*كده\s*',  # بعد كده
        r'وكمان\s*',  # وكمان
        r'ثم\s*',  # ثم
        r'بعدها\s*',  # بعدها
    ]
    
    # Combine all patterns
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    
    segments = re.split(combined_pattern, text, flags=re.IGNORECASE)
    
    # Clean segments and remove empty ones
    transactions = []
    for segment in segments:
        if segment and not re.match(r'^(وبعدين|و|بعد\s*كده|وكمان|ثم|بعدها)\s*$', segment.strip(), re.IGNORECASE):
            segment = segment.strip()
            if segment and len(segment) > 5:  # Ignore very short segments
                transactions.append(segment)
    
    # If no meaningful splits, try alternative approach
    if len(transactions) <= 1:
        # Look for amount patterns to split
        amount_positions = []
        for match in re.finditer(r'\d+\s*جنيه', text):
            amount_positions.append(match.end())
        
        if len(amount_positions) > 1:
            # Split after each amount mention
            segments = []
            start = 0
            for pos in amount_positions[:-1]:  # All except last
                segments.append(text[start:pos].strip())
                start = pos
            segments.append(text[start:].strip())  # Last segment
            
            transactions = [s for s in segments if s and len(s) > 5]
    
    # Final fallback - return whole text if still no good splits
    if len(transactions) <= 1:
        transactions = [text.strip()]
    
    logger.debug(f"Split into {len(transactions)} segments")
    return transactions


def detect_language(text: str) -> str:
    """Simple language detection for Arabic/English"""
    if not text:
        return "unknown"
    
    # Count Arabic characters
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
    total_chars = len([char for char in text if char.isalpha()])
    
    if total_chars == 0:
        return "unknown"
    
    arabic_ratio = arabic_chars / total_chars
    
    if arabic_ratio > 0.3:
        return "ar"
    elif arabic_ratio < 0.1:
        return "en"
    else:
        return "mixed"