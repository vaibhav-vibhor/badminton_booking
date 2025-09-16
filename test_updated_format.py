#!/usr/bin/env python3
"""
Test script to verify the updated table format with 24h time and no-slots messages
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_checker import BadmintonAPIChecker

async def test_updated_format():
    """Test the updated format with 24h time and no-slots handling"""
    print("🧪 Testing updated API table format...")
    
    # Create API checker instance
    api_checker = BadmintonAPIChecker()
    
    # Test dates - today, plus some future dates (including some that might not have slots)
    today = datetime.now().date()
    dates = [
        today.strftime('%Y-%m-%d'),
        (today + timedelta(days=1)).strftime('%Y-%m-%d'),
        (today + timedelta(days=2)).strftime('%Y-%m-%d'),
        (today + timedelta(days=6)).strftime('%Y-%m-%d'),  # Monday next week - might be empty
    ]
    
    print(f"📅 Testing dates: {', '.join(dates)}")
    
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
            print("📊 FORMATTED TELEGRAM MESSAGE (24h + No-Slots):")
            print("="*60)
            
            # Format results using the updated table format
            message = api_checker.format_results_for_telegram(results)
            print(message)
            
            print("\n" + "="*60)
            print("✅ Test completed successfully!")
            print("Key changes:")
            print("- Time format now uses 24h (12h → 12h, 1h → 01h, etc.)")
            print("- Dates with no available slots show '❌ No slots available'")
        else:
            print("❌ No results returned from API")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_updated_format())
