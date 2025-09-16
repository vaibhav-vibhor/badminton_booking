#!/usr/bin/env python3
"""
Test script to verify the new API table format for Telegram messages
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_checker import BadmintonAPIChecker

async def test_api_table_format():
    """Test the new table format"""
    print("🧪 Testing API table format...")
    
    # Create API checker instance
    api_checker = BadmintonAPIChecker()
    
    # Test dates - today, tomorrow, day after tomorrow
    today = datetime.now().date()
    dates = [
        today.strftime('%Y-%m-%d'),
        (today + timedelta(days=1)).strftime('%Y-%m-%d'),
        (today + timedelta(days=2)).strftime('%Y-%m-%d'),
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
            print("\n" + "="*50)
            print("📊 FORMATTED TELEGRAM MESSAGE:")
            print("="*50)
            
            # Format results using the new table format
            message = api_checker.format_results_for_telegram(results)
            print(message)
            
            print("\n" + "="*50)
            print("✅ Test completed successfully!")
        else:
            print("❌ No results returned from API")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_table_format())
