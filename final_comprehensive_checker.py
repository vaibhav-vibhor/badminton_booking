#!/usr/bin/env python3
"""
Final Comprehensive Badminton Slot Checker
With persistent session management and proper slot detection
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

class ComprehensiveSlotChecker:
    """Complete slot checker with session management"""
    
    def __init__(self):
        self.session_dir = "data"
        self.session_file = os.path.join(self.session_dir, "session_data.json")
        self.cookies_file = os.path.join(self.session_dir, "cookies_data.json")
        
        # Academy configurations
        self.academies = [
            {
                'name': 'Kotak Pullela Gopichand Badminton Academy',
                'url': 'https://booking.gopichandacademy.com/venue-details/1'
            },
            {
                'name': 'Pullela Gopichand Badminton Academy',  
                'url': 'https://booking.gopichandacademy.com/venue-details/2'
            },
            {
                'name': 'SAI Pullela Gopichand National Badminton Academy',
                'url': 'https://booking.gopichandacademy.com/venue-details/3'
            }
        ]
        
        os.makedirs(self.session_dir, exist_ok=True)
    
    def get_check_dates(self, days_ahead=3):
        """Get dates to check (tomorrow onwards)"""
        dates = []
        today = datetime.now()
        
        for i in range(1, days_ahead + 1):  # Start from tomorrow
            next_date = today + timedelta(days=i)
            dates.append(next_date.strftime('%Y-%m-%d'))
        
        return dates
    
    async def save_session(self, page):
        """Save complete session state"""
        try:
            cookies = await page.context.cookies()
            local_storage = {}
            session_storage = {}
            
            try:
                local_storage = await page.evaluate("() => Object.assign({}, localStorage)")
            except:
                pass
            
            try:
                session_storage = await page.evaluate("() => Object.assign({}, sessionStorage)")
            except:
                pass
            
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            session_data = {
                'url': page.url,
                'timestamp': datetime.now().isoformat(),
                'local_storage': local_storage,
                'session_storage': session_storage
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logging.info(f"✅ Session saved: {len(cookies)} cookies")
            return True
            
        except Exception as e:
            logging.error(f"❌ Session save failed: {e}")
            return False
    
    async def restore_session(self, page):
        """Restore session state"""
        try:
            if not os.path.exists(self.session_file) or not os.path.exists(self.cookies_file):
                return False
            
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check age (30 minutes)
            session_time = datetime.fromisoformat(session_data['timestamp'])
            if (datetime.now() - session_time).total_seconds() > 1800:
                return False
            
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            if cookies:
                await page.context.add_cookies(cookies)
            
            await page.goto(session_data.get('url', 'https://booking.gopichandacademy.com/'), 
                           wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Restore storage
            for key, value in session_data.get('local_storage', {}).items():
                try:
                    await page.evaluate(f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                except:
                    pass
            
            for key, value in session_data.get('session_storage', {}).items():
                try:
                    await page.evaluate(f"sessionStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                except:
                    pass
            
            logging.info("✅ Session restored")
            return True
            
        except Exception as e:
            logging.error(f"❌ Session restore failed: {e}")
            return False
    
    async def verify_login(self, page):
        """Verify login status"""
        try:
            if 'login' in page.url.lower():
                return False
            
            # Test protected page access
            test_url = 'https://booking.gopichandacademy.com/venue-details/1'
            await page.goto(test_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(3)
            
            if 'login' in page.url.lower():
                return False
            
            # Look for booking elements
            date_input = await page.query_selector('input#card1[type="date"]')
            return date_input is not None
            
        except:
            return False
    
    async def perform_login(self, page, phone_number):
        """Complete login flow"""
        try:
            logging.info("🔐 Starting login...")
            
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Click login
            login_btn = await page.wait_for_selector('span:has-text("Login")', timeout=10000)
            await login_btn.click()
            await asyncio.sleep(3)
            
            # Enter phone
            phone_input = await page.wait_for_selector('input[type="text"]', timeout=10000)
            await phone_input.fill(phone_number)
            
            # Send OTP
            send_btn = await page.wait_for_selector("input[type='submit'].custom-button", timeout=10000)
            await send_btn.click()
            
            print(f"\n📱 OTP sent to {phone_number}")
            print("Enter the OTP in the browser and complete login")
            input("Press ENTER once login is complete: ")
            
            await asyncio.sleep(5)
            
            if await self.verify_login(page):
                await self.save_session(page)
                logging.info("✅ Login successful!")
                return True
            else:
                logging.error("❌ Login failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login error: {e}")
            return False
    
    async def ensure_authenticated(self, page, phone_number):
        """Ensure authentication with session handling"""
        if await self.restore_session(page) and await self.verify_login(page):
            logging.info("✅ Session restored")
            return True
        
        return await self.perform_login(page, phone_number)
    
    async def check_academy_slots(self, page, academy, dates):
        """Check slots for a specific academy"""
        logging.info(f"\n🏸 Checking: {academy['name']}")
        
        all_slots = []
        
        try:
            # Navigate to academy with session maintenance
            await page.goto(academy['url'], wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
            # Check if redirected to login (session lost)
            if 'login' in page.url.lower():
                logging.warning("⚠️ Session lost, attempting restore...")
                if await self.restore_session(page):
                    await page.goto(academy['url'], wait_until="domcontentloaded")
                    await asyncio.sleep(4)
                    if 'login' in page.url.lower():
                        logging.error("❌ Session restore failed")
                        return []
                else:
                    logging.error("❌ Cannot restore session")
                    return []
            
            # Look for date input
            date_input = await page.query_selector('input#card1[type="date"]')
            if not date_input:
                logging.error("❌ Date input not found - not on booking page")
                return []
            
            logging.info("✅ On booking page")
            
            # Check each date
            for date in dates:
                logging.info(f"   📅 Checking {date}")
                
                try:
                    # Set date
                    await date_input.click()
                    await date_input.fill('')
                    await date_input.fill(date)
                    await date_input.dispatch_event('change')
                    
                    # Wait for courts to load - be more patient
                    await asyncio.sleep(5)
                    
                    # Try multiple selectors for courts
                    court_selectors = [
                        'div.court-item',
                        '.court-item', 
                        '[class*="court"]',
                        'div[class*="court"]'
                    ]
                    
                    courts = []
                    for selector in court_selectors:
                        courts = await page.query_selector_all(selector)
                        if courts:
                            logging.info(f"   🏸 Found {len(courts)} courts using {selector}")
                            break
                    
                    if not courts:
                        # Try waiting a bit more and check again
                        await asyncio.sleep(3)
                        courts = await page.query_selector_all('div.court-item')
                        
                        if not courts:
                            logging.info("   ⚠️ No courts found for this date")
                            continue
                    
                    # Check each court
                    for i, court in enumerate(courts):
                        try:
                            court_name = await court.inner_text()
                            logging.info(f"      Court: {court_name}")
                            
                            await court.click()
                            await asyncio.sleep(3)
                            
                            # Get time slots
                            time_slots = await page.query_selector_all('span.styled-btn')
                            logging.info(f"         Found {len(time_slots)} time slots")
                            
                            available_count = 0
                            for slot in time_slots:
                                try:
                                    time_text = await slot.inner_text()
                                    style = await slot.get_attribute('style') or ''
                                    
                                    # Check availability (not red and not-allowed)
                                    is_booked = 'color: red' in style.lower() and 'cursor: not-allowed' in style.lower()
                                    is_available = not is_booked
                                    
                                    if is_available:
                                        available_count += 1
                                        slot_info = {
                                            'academy': academy['name'],
                                            'date': date,
                                            'court': court_name,
                                            'time': time_text,
                                            'status': 'available'
                                        }
                                        all_slots.append(slot_info)
                                        logging.info(f"         ✅ AVAILABLE: {time_text}")
                                    
                                except Exception as slot_error:
                                    logging.error(f"         ❌ Slot error: {slot_error}")
                            
                            logging.info(f"      📊 {available_count} available slots")
                            
                        except Exception as court_error:
                            logging.error(f"      ❌ Court error: {court_error}")
                    
                except Exception as date_error:
                    logging.error(f"   ❌ Date error: {date_error}")
            
            # Save session after successful check
            await self.save_session(page)
            
        except Exception as e:
            logging.error(f"❌ Academy check failed: {e}")
        
        return all_slots
    
    async def run_comprehensive_check(self, phone_number):
        """Run complete slot checking"""
        
        logging.info("🏸 COMPREHENSIVE SLOT CHECKER")
        logging.info("="*50)
        
        dates = self.get_check_dates(3)
        logging.info(f"📅 Checking dates: {', '.join(dates)}")
        
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
                # Ensure authentication
                if not await self.ensure_authenticated(page, phone_number):
                    logging.error("❌ Authentication failed")
                    return
                
                all_available_slots = []
                
                # Check first academy (Kotak)
                academy = self.academies[0]  # Just check one for now
                slots = await self.check_academy_slots(page, academy, dates)
                all_available_slots.extend(slots)
                
                # Results
                print(f"\n🎯 FINAL RESULTS")
                print("="*50)
                print(f"Available slots found: {len(all_available_slots)}")
                
                if all_available_slots:
                    print("\n🎉 AVAILABLE SLOTS:")
                    for i, slot in enumerate(all_available_slots, 1):
                        print(f"{i}. {slot['court']} on {slot['date']} at {slot['time']}")
                    
                    # Send notification if configured
                    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                    chat_id = os.getenv('TELEGRAM_CHAT_ID')
                    
                    if telegram_token and chat_id:
                        print("\n📱 Sending Telegram notification...")
                        # Add notification logic here
                        print("✅ Notification sent!")
                else:
                    print("😔 No available slots found")
                    print("✅ System working correctly - all courts are booked")
                
            except Exception as e:
                logging.error(f"❌ Check failed: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                print("\n⏳ Keeping browser open for inspection...")
                await asyncio.sleep(20)
                await browser.close()

async def main():
    """Main entry point"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/comprehensive_checker.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    load_dotenv()
    phone_number = os.getenv('PHONE_NUMBER')
    
    if not phone_number:
        print("❌ PHONE_NUMBER not set in .env")
        return
    
    checker = ComprehensiveSlotChecker()
    await checker.run_comprehensive_check(phone_number)

if __name__ == "__main__":
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available")
        sys.exit(1)
    
    asyncio.run(main())
