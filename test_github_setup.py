#!/usr/bin/env python3
"""
Quick test script to verify GitHub Actions setup
"""

import os
import sys
import requests
from pathlib import Path

def test_environment():
    """Test that all environment variables are set"""
    print("🧪 Testing Environment Setup...")
    
    required_vars = ['PHONE_NUMBER', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * (len(value) - 4)}{value[-4:]}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Set these in your .env file (locally) or GitHub Secrets (for Actions)")
        return False
    
    return True

def test_telegram():
    """Test Telegram bot connection"""
    print("\n📱 Testing Telegram Connection...")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Telegram credentials not set")
        return False
    
    try:
        # Test bot info
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            bot_name = bot_info['result']['username']
            print(f"✅ Bot connected: @{bot_name}")
        else:
            print(f"❌ Bot token invalid: {response.status_code}")
            return False
        
        # Test sending message
        message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        test_message = {
            'chat_id': chat_id,
            'text': '🧪 GitHub Actions test successful!\n\nYour badminton checker is ready to run automatically every hour! 🏸',
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(message_url, json=test_message, timeout=10)
        
        if response.status_code == 200:
            print("✅ Test message sent to Telegram")
            return True
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print("Check your TELEGRAM_CHAT_ID is correct")
            return False
            
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")
        return False

def test_playwright():
    """Test if Playwright is available"""
    print("\n🎭 Testing Playwright...")
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright imported successfully")
        return True
    except ImportError:
        print("❌ Playwright not installed")
        print("Run: pip install playwright && playwright install chromium")
        return False

def test_session_directory():
    """Test session directory creation"""
    print("\n💾 Testing Session Directory...")
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    if data_dir.exists():
        print("✅ Data directory created")
        return True
    else:
        print("❌ Could not create data directory")
        return False

def main():
    """Run all tests"""
    print("🏸 GitHub Actions Badminton Checker - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Telegram Connection", test_telegram),
        ("Playwright Installation", test_playwright),
        ("Session Directory", test_session_directory)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Your GitHub Actions setup is ready!")
        print("\nNext steps:")
        print("1. Commit and push these files to GitHub")
        print("2. Go to Actions tab and enable workflows")
        print("3. Run the workflow manually to test")
        print("4. Your checker will run automatically every hour!")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("Check the GITHUB_ACTIONS_SETUP.md file for detailed instructions.")
    
    return all_passed

if __name__ == "__main__":
    # Load environment variables from .env if running locally
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    success = main()
    sys.exit(0 if success else 1)
