#!/usr/bin/env python3
"""
Local Session Setup for GitHub Actions
Run this locally once to establish a login session that GitHub Actions can use
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import the checker
from github_actions_checker import GitHubActionsChecker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalSessionSetup(GitHubActionsChecker):
    """Local version that can handle interactive login"""
    
    def __init__(self):
        super().__init__()
        
    async def interactive_login(self, page):
        """Handle interactive login with manual OTP entry"""
        try:
            logger.info("🌐 Starting login process...")
            await page.goto('https://booking.gopichandacademy.com/login', wait_until='networkidle')
            
            # Enter phone number
            phone_input = await page.wait_for_selector('input[type="tel"], input[name*="phone"], input[name*="mobile"]', timeout=10000)
            await phone_input.fill(self.phone_number)
            logger.info(f"📱 Phone number entered: {self.phone_number}")
            
            # Submit phone number
            submit_button = await page.query_selector('button[type="submit"], button:has-text("Send OTP"), .btn-primary')
            if submit_button:
                await submit_button.click()
                logger.info("📤 OTP request sent")
                await asyncio.sleep(3)
            
            # Wait for OTP input and manual entry
            logger.info("⏳ Waiting for manual OTP entry...")
            logger.info("👆 Please enter the OTP in the browser window that opened")
            logger.info("   The script will continue automatically once you're logged in...")
            
            # Wait for successful login (detect by URL change or dashboard elements)
            max_wait = 300  # 5 minutes
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_wait:
                current_url = page.url.lower()
                
                # Check if we're on a page that indicates login success
                if 'login' not in current_url or 'dashboard' in current_url or 'venue' in current_url:
                    try:
                        # Try to find elements that confirm we're logged in
                        profile_element = await page.query_selector('[class*="profile"], [class*="user"], [class*="logout"], [class*="avatar"]')
                        date_input = await page.query_selector('input[type="date"]')
                        
                        if profile_element or date_input:
                            logger.info("✅ Login successful!")
                            return True
                    except:
                        pass
                
                await asyncio.sleep(2)
            
            logger.error("❌ Login timeout - please try again")
            return False
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    async def setup_session(self):
        """Setup session for GitHub Actions"""
        logger.info("🔧 Setting up session for GitHub Actions...")
        logger.info("📱 This will open a browser window for manual login")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Use visible browser for local setup
            browser = await p.chromium.launch(
                headless=False,  # Show browser for manual interaction
                args=[
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Perform interactive login
                login_success = await self.interactive_login(page)
                
                if login_success:
                    # Save session data
                    await self.save_session(page)
                    
                    # Test the session
                    logger.info("🧪 Testing session...")
                    verify_success = await self.verify_login(page)
                    
                    if verify_success:
                        logger.info("🎉 Session setup complete!")
                        logger.info("✅ GitHub Actions will now be able to use this session")
                        logger.info("🚀 Your automated checker should work on the next run!")
                        
                        # Send success message
                        success_message = (
                            "✅ *Session Setup Complete!*\n\n"
                            "Your automated badminton checker is now ready!\n\n"
                            "🤖 GitHub Actions will use this session for hourly checks\n"
                            "📱 You'll get notifications when slots are found\n"
                            "⏰ Next check: Within the next hour\n\n"
                            "🎉 Setup successful! No more manual intervention needed."
                        )
                        self.send_telegram_message(success_message)
                        
                        return True
                    else:
                        logger.error("❌ Session verification failed")
                        return False
                else:
                    logger.error("❌ Login failed - session not created")
                    return False
                    
            finally:
                await browser.close()

async def main():
    """Main setup function"""
    try:
        print("\n🏸 Badminton Booking - GitHub Actions Session Setup")
        print("=" * 55)
        print("This script will help you set up a login session for GitHub Actions.")
        print("It will open a browser window where you need to manually login with OTP.")
        print("Once complete, GitHub Actions will run automatically every hour!\n")
        
        input("Press Enter to continue...")
        
        setup = LocalSessionSetup()
        success = await setup.setup_session()
        
        if success:
            print("\n🎉 SUCCESS! Your automated badminton checker is now ready!")
            print("GitHub Actions will handle everything automatically from now on.")
        else:
            print("\n❌ Setup failed. Please check the errors above and try again.")
            
    except KeyboardInterrupt:
        print("\n⚠️ Setup cancelled by user")
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
