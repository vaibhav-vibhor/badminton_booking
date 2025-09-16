#!/usr/bin/env python3
"""
Test script to verify the fixed table alignment with emojis
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_checker import BadmintonAPIChecker

async def test_alignment_fix():
    """Test the fixed alignment for emoji table"""
    print("🧪 Testing fixed table alignment...")
    
    # Create API checker instance
    api_checker = BadmintonAPIChecker()
    
    # Test dates - today only to keep output focused
    today = datetime.now().date()
    dates = [today.strftime('%Y-%m-%d')]
    
    print(f"📅 Testing date: {dates[0]}")
    
    try:
        # Load existing token
        if not api_checker.load_existing_token():
            print("❌ No existing token found. Please run the main script first to get a token.")
            return
        
        print("✅ Token loaded successfully")
        
        # Check all academies
        print("🏸 Checking all academies...")
        results = await api_checker.check_all_academies(dates)
        
        if results:
            print("\n" + "="*60)
            print("📊 FORMATTED TELEGRAM MESSAGE (FIXED ALIGNMENT):")
            print("="*60)
            
            # Format results using the fixed alignment
            message = api_checker.format_results_for_telegram(results)
            print(message)
            
            print("\n" + "="*60)
            print("✅ Alignment test completed!")
            print("Key improvements:")
            print("- Header spacing adjusted from 4 to 5 characters")
            print("- Court numbers reduced from 3 to 2 character width")
            print("- Emoji columns increased from 4 to 5 character width")
            print("- Should now show proper alignment between headers and emojis")
        else:
            print("❌ No results returned from API")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_alignment_fix())
