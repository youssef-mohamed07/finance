#!/usr/bin/env python3
"""
Quick test script to verify content filtering is working
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from utils.content_filter import content_filter
from exceptions import ValidationError

def test_content_filter():
    """Test the content filtering functionality"""
    
    print("🧪 Testing Content Filter...")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        # Should be BLOCKED
        ("انا اشتريت 3 كيلو حشيش مبارح", False, "Drug content (Arabic)"),
        ("I bought some cocaine yesterday", False, "Drug content (English)"),
        ("جبت 100 جنيه بانجو من كرفور", False, "Drug content with store"),
        ("تجارة المخدرات مربحة جداً", False, "Drug trafficking"),
        ("غسيل أموال في البنك", False, "Money laundering"),
        ("اشتريت مسدس بـ 500 دولار", False, "Weapons"),
        
        # Should be ALLOWED
        ("دفعت 50 جنيه في كارفور على خضار", True, "Legitimate grocery shopping"),
        ("استلمت مرتب 5000 جنيه", True, "Salary payment"),
        ("اشتريت قهوة بـ 25 جنيه", True, "Coffee purchase"),
        ("فاتورة الكهرباء 200 جنيه", True, "Utility bill"),
        ("ركبت تاكسي بـ 30 جنيه", True, "Transportation"),
        ("I paid 100 dollars for groceries", True, "English grocery shopping"),
        
        # Should be BLOCKED (non-financial)
        ("الطقس جميل اليوم", False, "Weather (non-financial)"),
        ("أحب مشاهدة الأفلام", False, "Movies (non-financial)"),
    ]
    
    passed = 0
    failed = 0
    
    for text, should_pass, description in test_cases:
        try:
            # Test content filtering
            content_filter.filter_text(text)
            
            # Test financial content detection
            is_financial = content_filter.is_financial_content(text)
            
            # Determine if it should pass (both content filter and financial check)
            actual_pass = is_financial
            
            if actual_pass == should_pass:
                print(f"✅ PASS: {description}")
                print(f"   Text: {text[:50]}...")
                print(f"   Expected: {'ALLOW' if should_pass else 'BLOCK'}, Got: {'ALLOW' if actual_pass else 'BLOCK'}")
                passed += 1
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Text: {text[:50]}...")
                print(f"   Expected: {'ALLOW' if should_pass else 'BLOCK'}, Got: {'ALLOW' if actual_pass else 'BLOCK'}")
                failed += 1
                
        except ValidationError as e:
            # Content was blocked by filter
            actual_pass = False
            
            if actual_pass == should_pass:
                print(f"✅ PASS: {description}")
                print(f"   Text: {text[:50]}...")
                print(f"   Blocked: {e.message}")
                passed += 1
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Text: {text[:50]}...")
                print(f"   Expected: {'ALLOW' if should_pass else 'BLOCK'}, Got: BLOCK")
                failed += 1
        
        print()
    
    print("=" * 50)
    print(f"📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Content filtering is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the content filtering logic.")
        return False

if __name__ == "__main__":
    success = test_content_filter()
    sys.exit(0 if success else 1)