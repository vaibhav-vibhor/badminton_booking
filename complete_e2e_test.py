#!/usr/bin/env python3
"""
Complete End-to-End Badminton Slot Checker
Tests: Login -> Session Management -> Slot Detection -> Telegram Notification
"""

import asyncio
import os
import sys
import json
import logging
import requests
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

class CompleteE2EChecker:
    """Complete end-to-end slot checker with Telegram notifications"""
    
    def __init__(self):
        self.session_dir = "data"
        self.session_file = os.path.join(self.session_dir, "e2e_session.json")
        self.cookies_file = os.path.join(self.session_dir, "e2e_cookies.json")
        
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
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/e2e_test.log'),
                logging.StreamHandler()
            ]
        )
    
    def send_telegram_message(self, message, token, chat_id):
        """Send message via Telegram Bot"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            logging.info("📱 Sending Telegram message...")
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logging.info("✅ Telegram message sent successfully!")
                return True
            else:
                logging.error(f"❌ Telegram send failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Telegram error: {e}")
            return False
    
    def format_slots_message(self, available_slots):
        """Format available slots for Telegram message"""
        if not available_slots:
            return "🏸 <b>Badminton Slot Checker</b> - Next Friday & Monday\n\n😔 No available slots found for the upcoming Friday and Monday.\nAll courts are currently booked."
        
        message = f"🏸 <b>Badminton Slot Checker</b> - Next Friday & Monday\n\n"
        message += f"🎉 <b>Found {len(available_slots)} Available Slots!</b>\n"
        message += f"📅 <i>Next upcoming Friday & Monday only</i>\n\n"
        
        # Group by date
        slots_by_date = {}
        for slot in available_slots:
            date = slot['date']
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(slot)
        
        for date, slots in sorted(slots_by_date.items()):
            # Format date nicely
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            
            message += f"📅 <b>{formatted_date}</b>\n"
            
            # Group by academy
            slots_by_academy = {}
            for slot in slots:
                academy = slot['academy']
                if academy not in slots_by_academy:
                    slots_by_academy[academy] = []
                slots_by_academy[academy].append(slot)
            
            for academy, academy_slots in slots_by_academy.items():
                academy_short = academy.replace('Pullela Gopichand Badminton Academy', 'PG Academy')
                message += f"  🏟️ <b>{academy_short}</b>\n"
                
                # Group by court
                slots_by_court = {}
                for slot in academy_slots:
                    court = slot['court']
                    if court not in slots_by_court:
                        slots_by_court[court] = []
                    slots_by_court[court].append(slot['time'])
                
                for court, times in sorted(slots_by_court.items()):
                    times_str = ', '.join(sorted(times))
                    message += f"    🏸 {court}: {times_str}\n"
            
            message += "\n"
        
        message += f"⏰ <i>Checked at {datetime.now().strftime('%H:%M:%S on %d/%m/%Y')}</i>"
        
        return message
    
    def get_check_dates(self, target_days=['friday', 'monday']):
        """Get next upcoming Friday and Monday dates (2 dates total)"""
        dates = []
        today = datetime.now()
        found_days = set()
        
        # Find the next upcoming Friday and Monday (one of each)
        for i in range(1, 15):  # Check next 2 weeks
            check_date = today + timedelta(days=i)
            weekday = check_date.strftime('%A').lower()
            
            if weekday in target_days and weekday not in found_days:
                dates.append(check_date.strftime('%Y-%m-%d'))
                found_days.add(weekday)
                
                # Stop once we have both Friday and Monday
                if len(found_days) == 2:
                    break
        
        # Sort dates chronologically
        dates.sort()
        return dates  # Next upcoming Friday and Monday only
    
    async def save_session(self, page):
        """Save session state"""
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
            
            logging.info(f"Session saved: {len(cookies)} cookies")
            return True
            
        except Exception as e:
            logging.error(f"Session save failed: {e}")
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
            
            logging.info("Session restored successfully")
            return True
            
        except Exception as e:
            logging.error(f"Session restore failed: {e}")
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
            logging.info("🔐 Starting login process...")
            
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Click login
            login_btn = await page.wait_for_selector('span:has-text("Login")', timeout=10000)
            await login_btn.click()
            await asyncio.sleep(3)
            logging.info("✅ Login button clicked")
            
            # Enter phone
            phone_input = await page.wait_for_selector('input[type="text"]', timeout=10000)
            await phone_input.fill(phone_number)
            logging.info(f"✅ Phone number entered: {phone_number}")
            
            # Send OTP
            send_btn = await page.wait_for_selector("input[type='submit'].custom-button", timeout=10000)
            await send_btn.click()
            logging.info("✅ OTP request sent")
            
            print(f"\n📱 OTP sent to {phone_number}")
            print("=" * 60)
            print("MANUAL OTP ENTRY REQUIRED")
            print("=" * 60)
            print("1. Check your phone for the OTP code")
            print("2. Enter the OTP in the browser")
            print("3. Click 'Verify' button")
            print("4. Wait for page to redirect")
            print("5. Press ENTER below once login is complete")
            print("=" * 60)
            
            input("Press ENTER once login is complete and redirected: ")
            
            await asyncio.sleep(5)
            
            if await self.verify_login(page):
                await self.save_session(page)
                logging.info("✅ Login successful and session saved!")
                return True
            else:
                logging.error("❌ Login verification failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login error: {e}")
            return False
    
    async def ensure_authenticated(self, page, phone_number):
        """Ensure authentication with session handling"""
        if await self.restore_session(page) and await self.verify_login(page):
            logging.info("✅ Session restored and verified")
            return True
        
        logging.info("🔄 Need fresh login...")
        return await self.perform_login(page, phone_number)
    
    async def navigate_with_retry(self, page, target_url, max_retries=3):
        """Navigate with session retry"""
        for attempt in range(max_retries):
            try:
                logging.info(f"🔗 Navigation attempt {attempt + 1} to: {target_url}")
                
                await self.save_session(page)
                await page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(4)
                
                if 'login' in page.url.lower():
                    if attempt < max_retries - 1:
                        logging.warning(f"⚠️ Session lost, attempting restore...")
                        if await self.restore_session(page):
                            continue
                    return False
                else:
                    date_input = await page.query_selector('input#card1[type="date"]')
                    if date_input:
                        logging.info("✅ Navigation successful")
                        return True
                    elif attempt < max_retries - 1:
                        await asyncio.sleep(3)
                        continue
                    return False
                    
            except Exception as e:
                logging.error(f"❌ Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        return False
    
    async def check_academy_slots(self, page, academy, dates):
        """Check slots for a specific academy"""
        logging.info(f"\n🏸 Checking: {academy['name']}")
        
        all_slots = []
        
        if not await self.navigate_with_retry(page, academy['url']):
            logging.error(f"❌ Failed to navigate to {academy['name']}")
            return []
        
        try:
            date_input = await page.wait_for_selector('input#card1[type="date"]', timeout=15000)
            if not date_input:
                logging.error("❌ Date input not found")
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
                    await asyncio.sleep(6)  # Wait for courts to load
                    
                    # Get courts
                    courts = await page.query_selector_all('div.court-item')
                    if not courts:
                        await asyncio.sleep(3)
                        courts = await page.query_selector_all('div.court-item')
                    
                    if not courts:
                        logging.info(f"   ⚠️ No courts found for {date}")
                        continue
                    
                    logging.info(f"   🏸 Found {len(courts)} courts")
                    
                    # Check each court
                    for court in courts:
                        try:
                            court_name = await court.inner_text()
                            logging.info(f"      Checking {court_name}")
                            
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
                                    
                                    # Check availability
                                    is_booked = ('color: red' in style.lower() and 
                                               'cursor: not-allowed' in style.lower())
                                    
                                    if not is_booked:
                                        available_count += 1
                                        slot_info = {
                                            'academy': academy['name'],
                                            'date': date,
                                            'court': court_name,
                                            'time': time_text,
                                            'status': 'available'
                                        }
                                        all_slots.append(slot_info)
                                        print(f"         AVAILABLE: {time_text}")
                                    
                                except Exception as slot_error:
                                    logging.error(f"         Slot error: {slot_error}")
                            
                            logging.info(f"      📊 {available_count} available slots")
                            
                        except Exception as court_error:
                            logging.error(f"      Court error: {court_error}")
                
                except Exception as date_error:
                    logging.error(f"   Date error: {date_error}")
            
            await self.save_session(page)
            
        except Exception as e:
            logging.error(f"❌ Academy check failed: {e}")
        
        return all_slots
    
    async def run_complete_e2e_test(self):
        """Run complete end-to-end test"""
        
        # Load environment
        load_dotenv()
        phone_number = os.getenv('PHONE_NUMBER')
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not phone_number:
            print("❌ PHONE_NUMBER not set in .env")
            return
        
        if not telegram_token or not chat_id:
            print("⚠️ Telegram configuration incomplete - notifications will be skipped")
        
        print("🏸 COMPLETE END-TO-END BADMINTON CHECKER")
        print("=" * 70)
        print(f"📱 Phone: {phone_number}")
        print(f"📡 Telegram: {'✅ Configured' if telegram_token and chat_id else '❌ Not configured'}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        dates = self.get_check_dates()
        # Format dates for display with day names
        date_display = []
        for date_str in dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted = date_obj.strftime('%A, %b %d (%Y-%m-%d)')
            date_display.append(formatted)
        
        print(f"📅 Checking next upcoming Friday & Monday only:")
        for date_info in date_display:
            print(f"   • {date_info}")
        print("=" * 70)
        
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
                print("\n🔐 AUTHENTICATION PHASE")
                print("-" * 40)
                
                # Ensure authentication
                if not await self.ensure_authenticated(page, phone_number):
                    print("❌ Authentication failed - cannot proceed")
                    return
                
                print("✅ Authentication successful!")
                
                print("\n🔍 SLOT CHECKING PHASE")
                print("-" * 40)
                
                all_available_slots = []
                
                # Check each academy
                for academy in self.academies:
                    slots = await self.check_academy_slots(page, academy, dates)
                    all_available_slots.extend(slots)
                    
                    if slots:
                        print(f"✅ {academy['name']}: {len(slots)} slots found")
                    else:
                        print(f"😔 {academy['name']}: No slots available")
                
                print("\n📊 RESULTS PHASE")
                print("-" * 40)
                
                print(f"🎯 Total available slots found: {len(all_available_slots)}")
                
                if all_available_slots:
                    print("\n🎉 AVAILABLE SLOTS:")
                    print("-" * 40)
                    
                    # Group and display results
                    slots_by_date = {}
                    for slot in all_available_slots:
                        date = slot['date']
                        if date not in slots_by_date:
                            slots_by_date[date] = []
                        slots_by_date[date].append(slot)
                    
                    for date, slots in sorted(slots_by_date.items()):
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%A, %B %d')
                        print(f"\n📅 {formatted_date}:")
                        
                        for slot in slots:
                            academy_short = slot['academy'].split(' ')[0]  # First word
                            print(f"   🏸 {academy_short} - {slot['court']} at {slot['time']}")
                
                print(f"\n📱 TELEGRAM NOTIFICATION PHASE")
                print("-" * 40)
                
                # Send Telegram notification
                if telegram_token and chat_id:
                    message = self.format_slots_message(all_available_slots)
                    
                    if self.send_telegram_message(message, telegram_token, chat_id):
                        print("✅ Telegram notification sent successfully!")
                    else:
                        print("❌ Telegram notification failed")
                else:
                    print("⚠️ Telegram not configured - skipping notification")
                
                print(f"\n✅ END-TO-END TEST COMPLETED")
                print("=" * 70)
                print(f"📊 Summary:")
                print(f"   • Total slots found: {len(all_available_slots)}")
                print(f"   • Academies checked: {len(self.academies)}")
                print(f"   • Dates checked: {len(dates)}")
                print(f"   • Telegram notification: {'✅ Sent' if telegram_token and chat_id else '❌ Skipped'}")
                print(f"   • Completed at: {datetime.now().strftime('%H:%M:%S')}")
                
            except Exception as e:
                logging.error(f"❌ E2E test failed: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                print(f"\n⏳ Keeping browser open for 30 seconds for inspection...")
                await asyncio.sleep(30)
                await browser.close()

async def main():
    """Main entry point"""
    os.makedirs('logs', exist_ok=True)
    
    checker = CompleteE2EChecker()
    await checker.run_complete_e2e_test()

if __name__ == "__main__":
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available")
        sys.exit(1)
    
    asyncio.run(main())
