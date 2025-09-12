#!/usr/bin/env python3
"""
Simple test script to verify all components work without real credentials
"""

import os
import sys
import asyncio
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from config_handler import ConfigHandler
        from login_handler import LoginHandler  
        from booking_checker import BookingChecker
        from academy_checker import AcademyChecker
        from notification_handler import NotificationHandler
        from slot_analyzer import SlotAnalyzer, DateTimeUtils, DataPersistence
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("\nTesting configuration...")
    try:
        # Set dummy environment variables
        os.environ['PHONE_NUMBER'] = '1234567890'
        os.environ['TELEGRAM_BOT_TOKEN'] = '123:test'
        os.environ['TELEGRAM_CHAT_ID'] = '123'
        
        from config_handler import ConfigHandler
        config = ConfigHandler()
        
        # Test academy configuration
        academies = config.academies
        assert len(academies) == 3
        assert 'kotak' in academies
        assert 'pullela' in academies
        assert 'sai' in academies
        
        print("✅ Configuration system working")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_utility_functions():
    """Test utility functions"""
    print("\nTesting utility functions...")
    try:
        from slot_analyzer import SlotAnalyzer, DateTimeUtils
        
        # Test time slot parsing
        time_slot = "18:00-19:00"
        parsed = SlotAnalyzer.parse_time_slot(time_slot)
        assert parsed['valid'] == True
        assert parsed['start'] == '18:00'
        assert parsed['end'] == '19:00'
        assert parsed['duration_minutes'] == 60
        
        # Test date utilities
        dates = DateTimeUtils.get_next_n_days(3)
        assert len(dates) == 3
        assert all(DateTimeUtils.is_valid_date(date) for date in dates)
        
        print("✅ Utility functions working")
        return True
        
    except Exception as e:
        print(f"❌ Utility function error: {e}")
        return False

def test_slot_processing():
    """Test slot processing logic"""
    print("\nTesting slot processing...")
    try:
        from booking_checker import BookingChecker
        
        checker = BookingChecker()
        
        # Test slot status detection
        available_style = ""
        booked_style = "color: red; cursor: not-allowed;"
        selected_style = "background: linear-gradient(...); color: white; cursor: pointer;"
        
        assert checker._determine_slot_status(available_style) == "available"
        assert checker._determine_slot_status(booked_style) == "booked" 
        assert checker._determine_slot_status(selected_style) == "selected"
        
        # Test duplicate removal
        test_slots = [
            {"academy": "Test", "date": "2025-09-13", "court": "Court 1", "time": "18:00-19:00"},
            {"academy": "Test", "date": "2025-09-13", "court": "Court 1", "time": "18:00-19:00"},  # duplicate
            {"academy": "Test", "date": "2025-09-13", "court": "Court 2", "time": "18:00-19:00"},
        ]
        
        unique_slots = checker.remove_duplicate_slots(test_slots)
        assert len(unique_slots) == 2
        
        print("✅ Slot processing working")
        return True
        
    except Exception as e:
        print(f"❌ Slot processing error: {e}")
        return False

async def test_playwright_integration():
    """Test Playwright integration"""
    print("\nTesting Playwright integration...")
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Test basic navigation
            await page.goto("https://google.com")
            title = await page.title()
            assert "Google" in title
            
            await browser.close()
        
        print("✅ Playwright integration working")
        return True
        
    except Exception as e:
        print(f"❌ Playwright error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🏸 Badminton Slot Checker - Component Tests")
    print("=" * 50)
    
    tests = [
        test_imports(),
        test_configuration(), 
        test_utility_functions(),
        test_slot_processing(),
        await test_playwright_integration()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 Test Results: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The badminton checker is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
