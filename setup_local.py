#!/usr/bin/env python3
"""
Setup script for local testing environment
"""

import os
import shutil
from pathlib import Path

def setup_local_env():
    """Setup local .env file for testing"""
    env_example = Path(__file__).parent / '.env.example'
    env_file = Path(__file__).parent / '.env'
    
    print("🏸 Badminton Checker - Local Setup")
    print("=" * 50)
    
    # Check if .env.example exists
    if not env_example.exists():
        print("❌ .env.example file not found!")
        return False
    
    # Check if .env already exists
    if env_file.exists():
        print("⚠️ .env file already exists")
        overwrite = input("Do you want to overwrite it? (y/n): ").lower().strip()
        if overwrite != 'y':
            print("✅ Keeping existing .env file")
            return True
    
    try:
        # Copy .env.example to .env
        shutil.copy2(env_example, env_file)
        print("✅ Created .env file from template")
        
        print("\n📝 Next steps:")
        print("1. Edit the .env file with your real credentials:")
        print("   • PHONE_NUMBER: Your phone number for login")
        print("   • TELEGRAM_BOT_TOKEN: Your bot token from @BotFather")
        print("   • TELEGRAM_CHAT_ID: Your chat ID (run get_chat_id.py to find it)")
        print("\n2. Run the local test:")
        print("   python run_local_test.py")
        print("\n🔒 Security Note: The .env file is already in .gitignore")
        print("   Your credentials will NOT be committed to the repository")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def show_credentials_help():
    """Show help for getting credentials"""
    print("\n📋 How to get your credentials:")
    print("\n1. 📱 PHONE_NUMBER:")
    print("   • Use the phone number you use to login to the badminton website")
    print("   • Format: Include country code (e.g., +1234567890)")
    print("\n2. 🤖 TELEGRAM_BOT_TOKEN:")
    print("   • Create a bot: Message @BotFather on Telegram")
    print("   • Send /newbot and follow instructions")
    print("   • Copy the token (format: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)")
    print("\n3. 💬 TELEGRAM_CHAT_ID:")
    print("   • Start a chat with your bot")
    print("   • Send any message to your bot")
    print("   • Run: python get_chat_id.py")
    print("   • Copy the chat ID")

if __name__ == "__main__":
    success = setup_local_env()
    
    if success:
        show_help = input("\nWould you like to see help for getting credentials? (y/n): ").lower().strip()
        if show_help == 'y':
            show_credentials_help()
    
    print("\n🚀 Ready to test locally!")
