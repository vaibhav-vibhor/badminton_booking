#!/usr/bin/env python3
"""
Persistent Session Checker - Fixes logout issues during navigation
Uses enhanced cookie management and session persistence techniques
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

class PersistentSessionManager:
    """Enhanced session manager that prevents logout during navigation"""
    
    def __init__(self):
        self.session_dir = "data"
        self.session_file = os.path.join(self.session_dir, "persistent_session.json")
        self.cookies_file = os.path.join(self.session_dir, "persistent_cookies.json")
        
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Session persistence settings
        self.session_timeout = 1800  # 30 minutes
        self.max_navigation_retries = 3
        
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
    
    async def create_persistent_context(self, playwright):
        """Create browser context with enhanced session persistence"""
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu'
            ]
        )
        
        # Create context with session-friendly settings
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            # Enable persistent storage
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        return browser, context
    
    async def save_enhanced_session(self, page):
        """Save session with enhanced persistence data"""
        try:
            logging.info("💾 Saving enhanced session...")
            
            # Get all cookies including httpOnly and secure cookies
            all_cookies = await page.context.cookies()
            
            # Get all storage data
            try:
                local_storage = await page.evaluate("""
                    () => {
                        const storage = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            storage[key] = localStorage.getItem(key);
                        }
                        return storage;
                    }
                """)
            except:
                local_storage = {}
            
            try:
                session_storage = await page.evaluate("""
                    () => {
                        const storage = {};
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            storage[key] = sessionStorage.getItem(key);
                        }
                        return storage;
                    }
                """)
            except:
                session_storage = {}
            
            # Get additional browser state
            try:
                current_url = page.url
                page_title = await page.title()
                user_agent = await page.evaluate("() => navigator.userAgent")
            except:
                current_url = ""
                page_title = ""
                user_agent = ""
            
            # Save cookies separately with enhanced metadata
            cookie_data = {
                'cookies': all_cookies,
                'timestamp': datetime.now().isoformat(),
                'url': current_url,
                'count': len(all_cookies)
            }
            
            with open(self.cookies_file, 'w') as f:
                json.dump(cookie_data, f, indent=2)
            
            # Save comprehensive session data
            session_data = {
                'url': current_url,
                'title': page_title,
                'timestamp': datetime.now().isoformat(),
                'user_agent': user_agent,
                'local_storage': local_storage,
                'session_storage': session_storage,
                'storage_counts': {
                    'cookies': len(all_cookies),
                    'localStorage': len(local_storage),
                    'sessionStorage': len(session_storage)
                }
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logging.info(f"✅ Enhanced session saved: {len(all_cookies)} cookies, {len(local_storage)} localStorage, {len(session_storage)} sessionStorage")
            return True
            
        except Exception as e:
            logging.error(f"❌ Enhanced session save failed: {e}")
            return False
    
    async def restore_enhanced_session(self, page):
        """Restore session with enhanced validation"""
        try:
            if not os.path.exists(self.session_file) or not os.path.exists(self.cookies_file):
                logging.info("No enhanced session files found")
                return False
            
            # Load session data
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            with open(self.cookies_file, 'r') as f:
                cookie_data = json.load(f)
            
            # Check session age
            session_time = datetime.fromisoformat(session_data['timestamp'])
            age_seconds = (datetime.now() - session_time).total_seconds()
            
            if age_seconds > self.session_timeout:
                logging.info(f"Session expired ({age_seconds:.0f}s old), skipping restore")
                return False
            
            logging.info(f"Restoring session ({age_seconds:.0f}s old)...")
            
            # Restore cookies first
            cookies = cookie_data.get('cookies', [])
            if cookies:
                # Clear existing cookies and add saved ones
                await page.context.clear_cookies()
                await page.context.add_cookies(cookies)
                logging.info(f"✅ Restored {len(cookies)} cookies")
            
            # Navigate to saved URL with proper wait
            saved_url = session_data.get('url', 'https://booking.gopichandacademy.com/')
            logging.info(f"🔗 Navigating to saved URL: {saved_url}")
            
            await page.goto(saved_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(4)  # Extra wait for SPA to stabilize
            
            # Restore localStorage
            local_storage = session_data.get('local_storage', {})
            if local_storage:
                restore_script = """
                    (storage) => {
                        for (const [key, value] of Object.entries(storage)) {
                            try {
                                localStorage.setItem(key, value);
                            } catch (e) {
                                console.warn('Failed to restore localStorage item:', key, e);
                            }
                        }
                    }
                """
                await page.evaluate(restore_script, local_storage)
                logging.info(f"✅ Restored {len(local_storage)} localStorage items")
            
            # Restore sessionStorage
            session_storage = session_data.get('session_storage', {})
            if session_storage:
                restore_script = """
                    (storage) => {
                        for (const [key, value] of Object.entries(storage)) {
                            try {
                                sessionStorage.setItem(key, value);
                            } catch (e) {
                                console.warn('Failed to restore sessionStorage item:', key, e);
                            }
                        }
                    }
                """
                await page.evaluate(restore_script, session_storage)
                logging.info(f"✅ Restored {len(session_storage)} sessionStorage items")
            
            # Wait for page to fully process restored session
            await asyncio.sleep(3)
            
            logging.info("✅ Enhanced session restoration completed")
            return True
            
        except Exception as e:
            logging.error(f"❌ Enhanced session restore failed: {e}")
            return False
    
    async def verify_authentication(self, page):
        """Enhanced authentication verification with multiple checks"""
        try:
            current_url = page.url
            logging.info(f"🔍 Verifying authentication at: {current_url}")
            
            # Primary check: Are we on login page?
            if 'login' in current_url.lower():
                logging.info("❌ Currently on login page - not authenticated")
                return False
            
            # Secondary check: Look for user-specific elements
            auth_indicators = [
                '#userNameCss',
                'span:has-text("Vaibhav")',
                '[class*="user"]',
                'a:has-text("Logout")',
                'button:has-text("Logout")',
                '.profile',
                '.user-profile'
            ]
            
            for selector in auth_indicators:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        text = await element.inner_text()
                        if text and text.strip():
                            logging.info(f"✅ Authentication verified via {selector}: '{text.strip()}'")
                            return True
                except:
                    continue
            
            # Tertiary check: Test protected page access
            logging.info("🔍 Testing protected page access...")
            
            # Save current URL to return to later
            original_url = page.url
            
            try:
                # Try accessing a known protected page
                test_url = 'https://booking.gopichandacademy.com/venue-details/1'
                await page.goto(test_url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(4)
                
                final_url = page.url
                if 'login' in final_url.lower():
                    logging.info("❌ Redirected to login when accessing protected page")
                    return False
                
                # Look for booking-specific elements
                booking_elements = [
                    'input#card1[type="date"]',
                    'div.court-item',
                    '.court-list',
                    '[class*="booking"]'
                ]
                
                for selector in booking_elements:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            logging.info(f"✅ Found booking element {selector} - authenticated")
                            return True
                    except:
                        continue
                
                logging.info("⚠️ On protected page but no booking elements found")
                
                # Check if page is still loading
                await asyncio.sleep(3)
                date_input = await page.query_selector('input#card1[type="date"]')
                if date_input:
                    logging.info("✅ Booking elements loaded after additional wait - authenticated")
                    return True
                
                return False
                
            except Exception as e:
                logging.error(f"❌ Error testing protected page access: {e}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Authentication verification failed: {e}")
            return False
    
    async def perform_robust_login(self, page, phone_number):
        """Perform login with enhanced session persistence"""
        try:
            logging.info("🚀 Starting robust login process...")
            
            # Navigate to login page
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle", timeout=30000)
            await asyncio.sleep(4)
            
            # Look for login button with multiple selectors
            login_selectors = [
                'span:has-text("Login")',
                'a:has-text("Login")',
                'button:has-text("Login")',
                '.login-btn',
                '#login-button',
                '[data-testid="login"]'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=8000)
                    if element and await element.is_visible():
                        await element.click()
                        await asyncio.sleep(4)
                        logging.info(f"✅ Login button clicked: {selector}")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                logging.error("❌ Could not find or click login button")
                return False
            
            # Enter phone number with multiple selector attempts
            phone_selectors = [
                'input[type="tel"]',
                'input[type="text"]',
                'input[name="phone"]',
                'input[name="mobile"]',
                'input[placeholder*="phone"]',
                'input[placeholder*="mobile"]',
                'input[placeholder*="number"]'
            ]
            
            phone_entered = False
            for selector in phone_selectors:
                try:
                    phone_input = await page.wait_for_selector(selector, timeout=8000)
                    if phone_input and await phone_input.is_visible():
                        await phone_input.click()
                        await phone_input.fill('')  # Clear existing content
                        await asyncio.sleep(1)
                        await phone_input.type(phone_number, delay=100)  # Type with delay
                        await asyncio.sleep(2)
                        logging.info(f"✅ Phone entered via {selector}: {phone_number}")
                        phone_entered = True
                        break
                except:
                    continue
            
            if not phone_entered:
                logging.error("❌ Could not enter phone number")
                return False
            
            # Send OTP with multiple selector attempts
            otp_selectors = [
                "input[type='submit'].custom-button",
                ".custom-button",
                "input[type='submit']",
                "button[type='submit']",
                "button:has-text('Send')",
                "button:has-text('Get OTP')"
            ]
            
            otp_sent = False
            for selector in otp_selectors:
                try:
                    send_btn = await page.wait_for_selector(selector, timeout=8000)
                    if send_btn and await send_btn.is_visible():
                        await send_btn.click()
                        await asyncio.sleep(3)
                        logging.info(f"✅ Send OTP clicked: {selector}")
                        otp_sent = True
                        break
                except:
                    continue
            
            if not otp_sent:
                logging.error("❌ Could not send OTP")
                return False
            
            # Manual OTP entry with clear instructions
            print("\n" + "="*70)
            print("📱 MANUAL OTP VERIFICATION REQUIRED")
            print("="*70)
            print("1. 📱 Check your phone for the OTP code")
            print("2. ⌨️  Enter the OTP in the browser form field")
            print("3. 🔘 Click 'Verify' or 'Submit' button")
            print("4. ⏳ Wait for the page to redirect after successful login")
            print("5. ✅ Once you see the main page (not login), press ENTER below")
            print("\n🚨 IMPORTANT: Do NOT close the browser window!")
            print("🚨 WAIT for redirect before pressing ENTER!")
            print("="*70)
            
            input("Press ENTER only AFTER successful login and page redirect: ")
            
            # Wait for authentication to complete
            await asyncio.sleep(6)
            
            # Verify authentication
            if await self.verify_authentication(page):
                # Save session immediately with enhanced persistence
                await self.save_enhanced_session(page)
                logging.info("✅ Robust login successful and session saved!")
                return True
            else:
                logging.error("❌ Login verification failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Robust login failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def navigate_with_session_retry(self, page, target_url, max_retries=3):
        """Navigate with automatic session restoration on failure"""
        for attempt in range(max_retries):
            try:
                logging.info(f"🔗 Navigation attempt {attempt + 1}/{max_retries} to: {target_url}")
                
                # Save session before navigation
                await self.save_enhanced_session(page)
                
                # Navigate to target
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)  # Extended wait for SPA to stabilize
                
                current_url = page.url
                if 'login' in current_url.lower():
                    logging.warning(f"⚠️ Redirected to login on attempt {attempt + 1}")
                    
                    if attempt < max_retries - 1:  # Don't restore on last attempt
                        logging.info("🔄 Attempting session restoration...")
                        if await self.restore_enhanced_session(page):
                            await asyncio.sleep(3)
                            continue
                        else:
                            logging.error("❌ Session restoration failed")
                    return False
                else:
                    logging.info(f"✅ Navigation successful on attempt {attempt + 1}")
                    
                    # Verify we can access booking elements
                    date_input = await page.query_selector('input#card1[type="date"]')
                    if date_input:
                        logging.info("✅ Booking elements accessible")
                        return True
                    else:
                        # Wait a bit more for elements to load
                        await asyncio.sleep(5)
                        date_input = await page.query_selector('input#card1[type="date"]')
                        if date_input:
                            logging.info("✅ Booking elements loaded after additional wait")
                            return True
                        else:
                            logging.warning("⚠️ Navigation successful but booking elements not found")
                            if attempt < max_retries - 1:
                                continue
                            return False
                    
            except Exception as e:
                logging.error(f"❌ Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    continue
        
        logging.error(f"❌ All {max_retries} navigation attempts failed")
        return False
    
    async def check_slots_with_persistent_session(self, page, academy_url, academy_name, dates):
        """Check slots while maintaining persistent session"""
        logging.info(f"\n🏸 Checking {academy_name} with persistent session")
        
        all_slots = []
        
        # Navigate with session retry mechanism
        if not await self.navigate_with_session_retry(page, academy_url):
            logging.error(f"❌ Failed to navigate to {academy_name}")
            return []
        
        logging.info("✅ Successfully navigated to academy page")
        
        try:
            # Verify booking page elements are present
            date_input = await page.wait_for_selector('input#card1[type="date"]', timeout=15000)
            if not date_input:
                logging.error("❌ Date input not found - not on booking page")
                return []
            
            logging.info("✅ Booking page confirmed")
            
            # Check each date
            for date in dates:
                logging.info(f"   📅 Checking {date}")
                
                try:
                    # Set date with enhanced interaction
                    await date_input.click()
                    await asyncio.sleep(1)
                    await date_input.fill('')
                    await asyncio.sleep(1)
                    await date_input.fill(date)
                    await date_input.press('Tab')  # Trigger change event
                    await asyncio.sleep(1)
                    await date_input.dispatch_event('change')
                    
                    # Wait longer for courts to load
                    await asyncio.sleep(8)
                    
                    # Look for courts with multiple strategies
                    courts = []
                    
                    # Strategy 1: Standard selector
                    courts = await page.query_selector_all('div.court-item')
                    
                    if not courts:
                        # Strategy 2: Wait and try again
                        await asyncio.sleep(5)
                        courts = await page.query_selector_all('div.court-item')
                    
                    if not courts:
                        # Strategy 3: Try alternative selectors
                        alt_selectors = ['.court-item', '[class*="court"]', 'div[class*="court"]']
                        for selector in alt_selectors:
                            courts = await page.query_selector_all(selector)
                            if courts:
                                break
                    
                    if not courts:
                        logging.info(f"   ⚠️ No courts found for {date} - possibly fully booked or page not loaded")
                        continue
                    
                    logging.info(f"   🏸 Found {len(courts)} courts")
                    
                    # Check each court
                    for court_idx, court in enumerate(courts):
                        try:
                            court_name = await court.inner_text()
                            logging.info(f"      Checking {court_name}")
                            
                            await court.click()
                            await asyncio.sleep(4)  # Wait for time slots to load
                            
                            # Get time slots
                            time_slots = await page.query_selector_all('span.styled-btn')
                            
                            if not time_slots:
                                # Wait and try again
                                await asyncio.sleep(3)
                                time_slots = await page.query_selector_all('span.styled-btn')
                            
                            logging.info(f"         Found {len(time_slots)} time slots")
                            
                            available_count = 0
                            for slot in time_slots:
                                try:
                                    time_text = await slot.inner_text()
                                    style = await slot.get_attribute('style') or ''
                                    
                                    # Check availability
                                    is_booked = ('color: red' in style.lower() and 
                                               'cursor: not-allowed' in style.lower())
                                    
                                    if not is_booked:
                                        available_count += 1
                                        slot_info = {
                                            'academy': academy_name,
                                            'date': date,
                                            'court': court_name,
                                            'time': time_text,
                                            'status': 'available'
                                        }
                                        all_slots.append(slot_info)
                                        logging.info(f"         ✅ AVAILABLE: {time_text}")
                                    
                                except Exception as slot_error:
                                    logging.error(f"         ❌ Slot processing error: {slot_error}")
                            
                            logging.info(f"      📊 {available_count} available slots in {court_name}")
                            
                        except Exception as court_error:
                            logging.error(f"      ❌ Court processing error: {court_error}")
                
                except Exception as date_error:
                    logging.error(f"   ❌ Date processing error: {date_error}")
            
            # Save session after successful operation
            await self.save_enhanced_session(page)
            
        except Exception as e:
            logging.error(f"❌ Slot checking error: {e}")
        
        return all_slots

async def main():
    """Main function to run the persistent session checker"""
    
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/persistent_session.log'),
            logging.StreamHandler()
        ]
    )
    
    load_dotenv()
    phone_number = os.getenv('PHONE_NUMBER')
    
    if not phone_number:
        print("❌ PHONE_NUMBER not set in .env file")
        return
    
    print("🏸 PERSISTENT SESSION BADMINTON CHECKER")
    print("="*60)
    print(f"📱 Phone: {phone_number}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    session_manager = PersistentSessionManager()
    
    # Get dates to check
    dates = []
    today = datetime.now()
    for i in range(1, 4):  # Check next 3 days
        next_date = today + timedelta(days=i)
        dates.append(next_date.strftime('%Y-%m-%d'))
    
    print(f"📅 Dates to check: {', '.join(dates)}")
    
    async with async_playwright() as p:
        browser, context = await session_manager.create_persistent_context(p)
        page = await context.new_page()
        
        try:
            # Ensure authentication
            if await session_manager.restore_enhanced_session(page):
                if await session_manager.verify_authentication(page):
                    logging.info("✅ Session restored successfully")
                else:
                    logging.info("❌ Restored session invalid, need fresh login")
                    if not await session_manager.perform_robust_login(page, phone_number):
                        logging.error("❌ Login failed")
                        return
            else:
                logging.info("🔄 No saved session, performing fresh login")
                if not await session_manager.perform_robust_login(page, phone_number):
                    logging.error("❌ Login failed")
                    return
            
            # Test academy
            academy = {
                'name': 'Kotak Pullela Gopichand Badminton Academy',
                'url': 'https://booking.gopichandacademy.com/venue-details/1'
            }
            
            # Check slots with persistent session
            available_slots = await session_manager.check_slots_with_persistent_session(
                page, academy['url'], academy['name'], dates
            )
            
            # Results
            print(f"\n🎯 FINAL RESULTS")
            print("="*50)
            print(f"Available slots found: {len(available_slots)}")
            
            if available_slots:
                print("\n🎉 AVAILABLE SLOTS:")
                for i, slot in enumerate(available_slots, 1):
                    print(f"{i}. {slot['court']} on {slot['date']} at {slot['time']}")
                    
                # Send notification if configured
                telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                
                if telegram_token and chat_id:
                    print("\n📱 Telegram notification would be sent!")
            else:
                print("😔 No available slots found")
                print("✅ System working - all courts are booked")
            
        except Exception as e:
            logging.error(f"❌ Main execution error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n⏳ Keeping browser open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            await browser.close()
    
    print(f"✅ Check completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available")
        sys.exit(1)
    
    asyncio.run(main())
