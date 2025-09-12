#!/usr/bin/env python3
"""
Comprehensive Session Manager for Badminton Booking
Handles login session persistence across page navigations
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("❌ Playwright not available. Install with: pip install playwright")
    PLAYWRIGHT_AVAILABLE = False
    sys.exit(1)

class SessionManager:
    """Manages persistent login sessions"""
    
    def __init__(self):
        self.session_dir = "data"
        self.session_file = os.path.join(self.session_dir, "session_data.json")
        self.cookies_file = os.path.join(self.session_dir, "cookies_data.json")
        
        # Ensure data directory exists
        os.makedirs(self.session_dir, exist_ok=True)
        
    async def save_complete_session(self, page):
        """Save complete session including cookies, storage, and page state"""
        try:
            logging.info("💾 Saving complete session...")
            
            # Get all cookies
            cookies = await page.context.cookies()
            
            # Get storage data
            local_storage = {}
            session_storage = {}
            
            try:
                local_storage = await page.evaluate("() => Object.assign({}, localStorage)")
            except:
                logging.warning("Could not access localStorage")
            
            try:
                session_storage = await page.evaluate("() => Object.assign({}, sessionStorage)")
            except:
                logging.warning("Could not access sessionStorage")
            
            # Save cookies separately for better management
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            # Save session data
            session_data = {
                'url': page.url,
                'timestamp': datetime.now().isoformat(),
                'local_storage': local_storage,
                'session_storage': session_storage,
                'user_agent': await page.evaluate("() => navigator.userAgent"),
                'page_title': await page.title()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logging.info(f"✅ Session saved: {len(cookies)} cookies, {len(local_storage)} localStorage items")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to save session: {e}")
            return False
    
    async def restore_complete_session(self, page):
        """Restore complete session with validation"""
        try:
            if not os.path.exists(self.session_file) or not os.path.exists(self.cookies_file):
                logging.info("No saved session found")
                return False
            
            # Load session data
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check session age (30 minutes max)
            session_time = datetime.fromisoformat(session_data['timestamp'])
            age_seconds = (datetime.now() - session_time).total_seconds()
            
            if age_seconds > 1800:  # 30 minutes
                logging.info(f"Session too old ({age_seconds:.0f}s), will not restore")
                return False
            
            # Load cookies
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Add cookies to context
            if cookies:
                await page.context.add_cookies(cookies)
                logging.info(f"✅ Restored {len(cookies)} cookies")
            
            # Navigate to saved URL
            saved_url = session_data.get('url', 'https://booking.gopichandacademy.com/')
            await page.goto(saved_url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Restore localStorage
            if session_data.get('local_storage'):
                for key, value in session_data['local_storage'].items():
                    try:
                        await page.evaluate(f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                    except:
                        pass
            
            # Restore sessionStorage
            if session_data.get('session_storage'):
                for key, value in session_data['session_storage'].items():
                    try:
                        await page.evaluate(f"sessionStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                    except:
                        pass
            
            logging.info("✅ Session restoration completed")
            return True
            
        except Exception as e:
            logging.error(f"❌ Session restoration failed: {e}")
            return False
    
    async def verify_logged_in(self, page):
        """Comprehensive login status verification"""
        try:
            current_url = page.url
            logging.info(f"🔍 Verifying login status at: {current_url}")
            
            # Check if we're on login page
            if 'login' in current_url.lower():
                logging.info("❌ Currently on login page")
                return False
            
            # Look for login indicators
            login_indicators = [
                '#userNameCss',
                'span:has-text("Vaibhav")',
                '[class*="user"]',
                'a:has-text("Logout")',
                'button:has-text("Logout")',
                '.user-name',
                '.profile'
            ]
            
            for selector in login_indicators:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if text and text.strip():
                            logging.info(f"✅ Login verified via {selector}: '{text.strip()}'")
                            return True
                except:
                    continue
            
            # Test access to protected page
            try:
                logging.info("🔍 Testing protected page access...")
                test_url = 'https://booking.gopichandacademy.com/venue-details/1'
                
                response = await page.goto(test_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
                
                final_url = page.url
                if 'login' in final_url.lower():
                    logging.info("❌ Redirected to login - not authenticated")
                    return False
                
                # Look for booking page elements
                booking_indicators = [
                    'input#card1[type="date"]',
                    'div.court-item',
                    '.booking-form',
                    '[class*="court"]'
                ]
                
                for selector in booking_indicators:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            logging.info(f"✅ Found booking element {selector} - authenticated")
                            return True
                    except:
                        continue
                
                logging.info("⚠️ On protected page but no booking elements found")
                return False
                
            except Exception as e:
                logging.error(f"❌ Error testing protected page: {e}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login verification error: {e}")
            return False
    
    async def ensure_authenticated(self, page, phone_number):
        """Ensure user is authenticated, handling session restoration or fresh login"""
        try:
            logging.info("🔐 Ensuring authentication...")
            
            # Try to restore existing session first
            if await self.restore_complete_session(page):
                if await self.verify_logged_in(page):
                    logging.info("✅ Session restored and verified")
                    return True
                else:
                    logging.info("❌ Restored session is invalid")
            
            # Need fresh login
            logging.info("🔄 Performing fresh login...")
            return await self.perform_login(page, phone_number)
            
        except Exception as e:
            logging.error(f"❌ Authentication error: {e}")
            return False
    
    async def perform_login(self, page, phone_number):
        """Perform complete login flow"""
        try:
            logging.info("🚀 Starting fresh login...")
            
            # Navigate to home page
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Find and click login
            login_selectors = [
                'span:has-text("Login")',
                'a:has-text("Login")',
                'button:has-text("Login")',
                '.login',
                '#login'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        await element.click()
                        await asyncio.sleep(3)
                        logging.info(f"✅ Login clicked: {selector}")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                logging.error("❌ Could not find login button")
                return False
            
            # Enter phone number
            phone_selectors = [
                'input[type="tel"]',
                'input[type="text"]',
                'input[placeholder*="phone"]',
                'input[placeholder*="mobile"]',
                'input'
            ]
            
            phone_entered = False
            for selector in phone_selectors:
                try:
                    phone_input = await page.wait_for_selector(selector, timeout=5000)
                    if phone_input and await phone_input.is_visible():
                        await phone_input.click()
                        await phone_input.fill('')
                        await phone_input.type(phone_number)
                        logging.info(f"✅ Phone entered via {selector}: {phone_number}")
                        phone_entered = True
                        break
                except:
                    continue
            
            if not phone_entered:
                logging.error("❌ Could not enter phone number")
                return False
            
            # Click Send OTP
            otp_selectors = [
                "input[type='submit'].custom-button",
                ".custom-button",
                "input[type='submit']",
                "button[type='submit']",
                "button:has-text('Send')"
            ]
            
            otp_sent = False
            for selector in otp_selectors:
                try:
                    send_btn = await page.wait_for_selector(selector, timeout=5000)
                    if send_btn and await send_btn.is_visible():
                        await send_btn.click()
                        logging.info(f"✅ Send OTP clicked: {selector}")
                        otp_sent = True
                        break
                except:
                    continue
            
            if not otp_sent:
                logging.error("❌ Could not send OTP")
                return False
            
            # Manual OTP entry
            print("\n" + "="*60)
            print("📱 MANUAL OTP ENTRY REQUIRED")
            print("="*60)
            print("1. Check your phone for the OTP code")
            print("2. Enter the OTP in the browser form field")
            print("3. Click 'Verify' or 'Submit' button")
            print("4. Wait for the page to redirect")
            print("5. Press ENTER below once login is complete")
            print("\nIMPORTANT: Keep the browser window open!")
            print("="*60)
            
            input("Press ENTER once you've completed login and page has redirected: ")
            
            # Verify login success
            await asyncio.sleep(5)
            
            if await self.verify_logged_in(page):
                # Save session immediately after successful login
                await self.save_complete_session(page)
                logging.info("✅ Login successful and session saved!")
                return True
            else:
                logging.error("❌ Login verification failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login process failed: {e}")
            return False
    
    async def navigate_with_session_maintenance(self, page, target_url):
        """Navigate while maintaining session, with fallback recovery"""
        try:
            logging.info(f"🔗 Navigating to: {target_url}")
            
            # Save current session before navigation
            await self.save_complete_session(page)
            
            # Navigate
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
            # Check if we lost session (redirected to login)
            current_url = page.url
            if 'login' in current_url.lower():
                logging.warning("⚠️ Session lost during navigation, attempting recovery...")
                
                # Try to restore session and navigate again
                if await self.restore_complete_session(page):
                    await asyncio.sleep(2)
                    await page.goto(target_url, wait_until="domcontentloaded")
                    await asyncio.sleep(3)
                    
                    if 'login' not in page.url.lower():
                        logging.info("✅ Session recovered successfully")
                        return True
                    else:
                        logging.error("❌ Session recovery failed")
                        return False
                else:
                    logging.error("❌ Could not restore session")
                    return False
            else:
                logging.info("✅ Navigation successful - session maintained")
                return True
                
        except Exception as e:
            logging.error(f"❌ Navigation failed: {e}")
            return False

async def test_session_manager():
    """Test the session manager with actual booking flow"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    load_dotenv()
    phone_number = os.getenv('PHONE_NUMBER')
    
    if not phone_number:
        print("❌ PHONE_NUMBER not set in .env file")
        return
    
    print("🏸 SESSION MANAGER TEST")
    print("="*50)
    print(f"📱 Phone: {phone_number}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    session_manager = SessionManager()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Test authentication
            if await session_manager.ensure_authenticated(page, phone_number):
                print("✅ Authentication successful!")
                
                # Test navigation to booking page
                academy_url = 'https://booking.gopichandacademy.com/venue-details/1'
                if await session_manager.navigate_with_session_maintenance(page, academy_url):
                    print("✅ Navigation successful!")
                    
                    # Look for booking elements
                    date_input = await page.query_selector('input#card1[type="date"]')
                    if date_input:
                        print("✅ Booking page elements found!")
                        
                        # Test setting a date
                        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                        await date_input.fill(tomorrow)
                        await date_input.dispatch_event('change')
                        await asyncio.sleep(3)
                        
                        # Check for courts
                        courts = await page.query_selector_all('div.court-item')
                        print(f"🏸 Found {len(courts)} courts")
                        
                        if courts:
                            print("✅ Complete booking flow working!")
                        else:
                            print("⚠️ No courts found - may be fully booked")
                    else:
                        print("❌ Booking elements not found")
                else:
                    print("❌ Navigation failed")
            else:
                print("❌ Authentication failed")
            
        except Exception as e:
            logging.error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n⏳ Keeping browser open for 15 seconds...")
            await asyncio.sleep(15)
            await browser.close()
    
    print("✅ Test completed")

if __name__ == "__main__":
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available")
        sys.exit(1)
        
    asyncio.run(test_session_manager())
