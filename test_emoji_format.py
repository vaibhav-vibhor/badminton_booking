#!/usr/bin/env python3
"""
Test script to verify the emoji format with green ticks and red crosses
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_checker import BadmintonAPIChecker

async def test_emoji_format():
    """Test the emoji format with green ticks and red crosses"""
    print("🧪 Testing emoji format (✅ green ticks, ❌ red crosses)...")
    
    # Create API checker instance
    api_checker = BadmintonAPIChecker()
    
    # Test dates - today and tomorrow
    today = datetime.now().date()
    dates = [
        today.strftime('%Y-%m-%d'),
        (today + timedelta(days=1)).strftime('%Y-%m-%d'),
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
            print("📊 FORMATTED TELEGRAM MESSAGE (WITH EMOJIS):")
            print("="*60)
            
            # Format results using the updated emoji format
            message = api_checker.format_results_for_telegram(results)
            print(message)
            
            print("\n" + "="*60)
            print("✅ Test completed successfully!")
            print("Key changes:")
            print("- Available slots: ✅ (green tick emoji)")
            print("- Booked slots: ❌ (red cross emoji)")
            print("- Much more visually appealing and easier to read!")
        else:
            print("❌ No results returned from API")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_emoji_format())
