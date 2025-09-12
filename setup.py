#!/usr/bin/env python3
"""
Setup script for Badminton Booking Slot Checker
Helps users configure the system for first-time use
"""

import os
import sys
import json
from datetime import datetime

def print_header():
    """Print the setup header"""
    print("🏸 Badminton Slot Checker - Setup Guide")
    print("=" * 50)
    print("This script will help you set up the badminton booking checker.")
    print("You'll need to create a Telegram bot and configure your preferences.\n")

def create_env_file():
    """Create .env file template"""
    env_content = """# Badminton Booking Checker Configuration

# Your phone number for login (format: 1234567890)
PHONE_NUMBER=

# Telegram Bot Configuration
# Create a bot by messaging @BotFather on Telegram
TELEGRAM_BOT_TOKEN=

# Your Telegram Chat ID (message @userinfobot to get this)
TELEGRAM_CHAT_ID=

# Optional: Set to 'true' to run in test mode
# TEST_MODE=false

# Optional: Custom time preferences (comma-separated, e.g., 18:00-19:00,19:00-20:00)
# PREFERRED_TIMES=
"""
    
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} already exists. Backup created as {env_file}.backup")
        os.rename(env_file, f"{env_file}.backup")
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Created {env_file} template")
    return env_file

def show_telegram_setup():
    """Show Telegram bot setup instructions"""
    print("\n📱 Telegram Bot Setup Instructions:")
    print("-" * 40)
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot and follow the prompts")
    print("3. Choose a name for your bot (e.g., 'Badminton Checker Bot')")
    print("4. Choose a username (e.g., 'your_badminton_bot')")
    print("5. Copy the bot token (looks like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)")
    print("6. Message @userinfobot to get your chat ID")
    print("7. Add both values to your .env file")

def show_date_config():
    """Show date configuration instructions"""
    print("\n📅 Date Configuration:")
    print("-" * 25)
    print("Edit config/check_dates.json to specify which dates to check:")
    print("- Use 'today', 'tomorrow', or specific dates like '2025-01-15'")
    print("- The system will automatically check the next 7 days by default")

def show_github_setup():
    """Show GitHub Actions setup instructions"""
    print("\n🚀 GitHub Actions Setup (Free Hosting):")
    print("-" * 45)
    print("1. Create a GitHub repository and upload your code")
    print("2. Go to Settings > Secrets and variables > Actions")
    print("3. Add these repository secrets:")
    print("   - PHONE_NUMBER: Your phone number")
    print("   - TELEGRAM_BOT_TOKEN: Your bot token")  
    print("   - TELEGRAM_CHAT_ID: Your chat ID")
    print("4. Enable GitHub Actions in the Actions tab")
    print("5. The workflow will run every 15 minutes automatically!")

def run_quick_test():
    """Run a quick test to verify setup"""
    print("\n🔧 Quick Test:")
    print("-" * 15)
    
    # Check if main components exist
    required_files = [
        'src/main.py',
        'config/settings.json',
        'config/check_dates.json',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    
    # Test imports
    sys.path.insert(0, 'src')
    try:
        from main import BadmintonSlotChecker
        print("✅ Main modules can be imported")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print_header()
    
    # Create .env file
    env_file = create_env_file()
    
    # Show setup instructions
    show_telegram_setup()
    show_date_config()
    show_github_setup()
    
    # Run quick test
    if run_quick_test():
        print("\n🎉 Setup Complete!")
        print("-" * 20)
        print(f"1. Edit {env_file} with your credentials")
        print("2. Customize config/check_dates.json for your preferred dates")
        print("3. Test locally: python src/main.py --mode test")
        print("4. Deploy to GitHub Actions for automatic checking!")
        print("\n📖 See README.md for detailed instructions")
    else:
        print("\n❌ Setup issues detected. Please check the errors above.")

if __name__ == "__main__":
    main()
