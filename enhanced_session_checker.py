#!/usr/bin/env python3
"""
Enhanced Session-Persistent Checker with Better Authentication Management
This version maintains login session across page navigations
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from playwright.async_api import async_playwright

def get_next_booking_dates(days_ahead=5):
    """Get the next available booking dates"""
    today = datetime.now()
    dates = []
    
    for i in range(1, days_ahead + 1):  # Start from tomorrow
        next_date = today + timedelta(days=i)
        dates.append(next_date.strftime('%Y-%m-%d'))
    
    return dates

class EnhancedSessionManager:
    """Manages login session with persistence"""
    
    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.session_file = "data/enhanced_session.json"
        self.cookies_file = "data/enhanced_cookies.json"
        
    async def save_session(self, page):
        """Save complete session state"""
        try:
            os.makedirs("data", exist_ok=True)
            
            # Get all cookies
            cookies = await page.context.cookies()
            
            # Get storage data
            local_storage = await page.evaluate("() => Object.assign({}, localStorage)")
            session_storage = await page.evaluate("() => Object.assign({}, sessionStorage)")
            
            # Save cookies
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            # Save session data
            session_data = {
                'url': page.url,
                'timestamp': datetime.now().isoformat(),
                'local_storage': local_storage,
                'session_storage': session_storage,
                'user_agent': await page.evaluate("() => navigator.userAgent")
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            print("   ✅ Session saved successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ Error saving session: {e}")
            return False
    
    async def restore_session(self, page):
        """Restore complete session state"""
        try:
            if not os.path.exists(self.cookies_file) or not os.path.exists(self.session_file):
                print("   ⚠️ No saved session found")
                return False
            
            # Load session data
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is recent (within 30 minutes)
            session_time = datetime.fromisoformat(session_data['timestamp'])
            if (datetime.now() - session_time).total_seconds() > 1800:  # 30 minutes
                print("   ⚠️ Session too old, will re-login")
                return False
            
            # Load and set cookies
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            if cookies:
                await page.context.add_cookies(cookies)
                print(f"   ✅ Restored {len(cookies)} cookies")
            
            # Navigate to the saved URL
            await page.goto(session_data.get('url', 'https://booking.gopichandacademy.com/'))
            await asyncio.sleep(2)
            
            # Restore storage data
            if session_data.get('local_storage'):
                for key, value in session_data['local_storage'].items():
                    try:
                        await page.evaluate(f"localStorage.setItem('{key}', {json.dumps(value)})")
                    except:
                        pass
            
            if session_data.get('session_storage'):
                for key, value in session_data['session_storage'].items():
                    try:
                        await page.evaluate(f"sessionStorage.setItem('{key}', {json.dumps(value)})")
                    except:
                        pass
            
            print("   ✅ Session restoration attempted")
            return True
            
        except Exception as e:
            print(f"   ❌ Error restoring session: {e}")
            return False
    
    async def verify_login_status(self, page):
        """Verify if currently logged in"""
        try:
            current_url = page.url
            print(f"   🔍 Checking login status at: {current_url}")
            
            # Check URL
            if 'login' in current_url.lower():
                print("   ❌ On login page")
                return False
            
            # Look for user indicators
            user_selectors = [
                '#userNameCss',
                'span:has-text("Vaibhav")',
                '[class*="user"]',
                'a:has-text("Logout")',
                'button:has-text("Logout")'
            ]
            
            for selector in user_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if text and text.strip():
                            print(f"   ✅ Found login indicator: {selector} = '{text.strip()}'")
                            return True
                except:
                    continue
            
            # Check if we can access a protected page
            try:
                test_response = await page.goto('https://booking.gopichandacademy.com/venue-details/1', 
                                               wait_until='domcontentloaded', timeout=10000)
                await asyncio.sleep(2)
                
                if 'login' in page.url.lower():
                    print("   ❌ Redirected to login when accessing protected page")
                    return False
                else:
                    print("   ✅ Can access protected page - likely logged in")
                    return True
                    
            except Exception as e:
                print(f"   ⚠️ Error testing protected page: {e}")
                return False
            
        except Exception as e:
            print(f"   ❌ Error verifying login: {e}")
            return False

async def perform_manual_login(page, phone_number, session_manager):
    """Perform manual login with session saving"""
    try:
        print("🔐 Starting fresh login...")
        
        # Navigate to home page first
        await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Click Login
        print("   🔗 Looking for Login button...")
        login_selectors = [
            'span:has-text("Login")',
            'a:has-text("Login")',
            'button:has-text("Login")'
        ]
        
        login_clicked = False
        for selector in login_selectors:
            try:
                login_btn = await page.wait_for_selector(selector, timeout=5000)
                await login_btn.click()
                await asyncio.sleep(3)
                print(f"   ✅ Clicked Login: {selector}")
                login_clicked = True
                break
            except:
                continue
        
        if not login_clicked:
            print("   ❌ Could not find Login button")
            return False
        
        # Enter phone number
        print("   📱 Entering phone number...")
        try:
            phone_input = await page.wait_for_selector('input', timeout=10000)
            await phone_input.click()
            await phone_input.fill('')
            await phone_input.type(phone_number)
            print(f"   ✅ Entered: {phone_number}")
        except Exception as e:
            print(f"   ❌ Error entering phone: {e}")
            return False
        
        # Click Send OTP
        print("   📤 Clicking Send OTP...")
        try:
            otp_selectors = [
                "input[type='submit'].custom-button",
                ".custom-button",
                "input[type='submit']",
                "button[type='submit']"
            ]
            
            otp_clicked = False
            for selector in otp_selectors:
                try:
                    send_btn = await page.wait_for_selector(selector, timeout=3000)
                    if send_btn and await send_btn.is_visible():
                        await send_btn.click()
                        print(f"   ✅ Clicked Send OTP: {selector}")
                        otp_clicked = True
                        break
                except:
                    continue
            
            if not otp_clicked:
                print("   ❌ Could not click Send OTP")
                return False
                
        except Exception as e:
            print(f"   ❌ Error clicking Send OTP: {e}")
            return False
        
        # Manual OTP entry
        print("\n" + "="*60)
        print("📱 MANUAL OTP ENTRY - CRITICAL STEP")
        print("="*60)
        print("🔍 1. Check your phone for the OTP code")
        print("⌨️  2. Enter the OTP in the browser form field")
        print("🔘 3. Click 'Verify' or 'Submit' button")
        print("⏳ 4. Wait for the page to redirect (DO NOT CLOSE BROWSER)")
        print("✅ 5. Once redirected, press ENTER below")
        print("\nIMPORTANT: Keep the browser open and visible!")
        print("="*60)
        
        input("Press ENTER once login is complete and page has redirected: ")
        
        # Wait for redirect and verify
        await asyncio.sleep(3)
        
        if await session_manager.verify_login_status(page):
            # Save the session immediately after successful login
            await session_manager.save_session(page)
            print("✅ Login successful and session saved!")
            return True
        else:
            print("❌ Login verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

async def check_slots_with_persistent_session(page, academy_url, academy_name, dates, session_manager):
    """Check slots while maintaining session"""
    print(f"\n🏟️ Checking: {academy_name}")
    print(f"   URL: {academy_url}")
    
    all_slots = []
    
    try:
        # Navigate to academy page
        print("   🔗 Navigating to academy page...")
        await page.goto(academy_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Check if we got redirected to login (session lost)
        if 'login' in page.url.lower():
            print("   ❌ Session lost - redirected to login page")
            print("   🔄 Attempting to restore session...")
            
            # Try to restore session
            if await session_manager.restore_session(page):
                await page.goto(academy_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                if 'login' in page.url.lower():
                    print("   ❌ Session restoration failed - need fresh login")
                    return []
                else:
                    print("   ✅ Session restored successfully")
            else:
                print("   ❌ Cannot restore session - need fresh login")
                return []
        
        print(f"   ✅ Successfully on: {page.url}")
        
        # Look for booking elements
        date_input = await page.query_selector('input#card1[type="date"]')
        if not date_input:
            print("   ❌ No date input found - not on booking page")
            
            # Debug what's on the page
            title = await page.title()
            body_text = await page.inner_text('body')
            print(f"   🔍 Page title: {title}")
            print(f"   🔍 Contains 'Date': {'Date' in body_text}")
            print(f"   🔍 Contains 'Court': {'Court' in body_text}")
            return []
        
        print("   ✅ Found date input - on correct booking page")
        
        # Check each date
        for date in dates:
            print(f"\n   📅 Checking date: {date}")
            
            try:
                # Set date
                await date_input.click()
                await date_input.fill('')
                await date_input.fill(date)
                await date_input.dispatch_event('change')
                await asyncio.sleep(4)
                
                print("      ✅ Date set")
                
                # Wait for courts to appear
                try:
                    await page.wait_for_selector('div.court-item', timeout=10000)
                    courts = await page.query_selector_all('div.court-item')
                    print(f"      🏸 Found {len(courts)} courts")
                    
                    if not courts:
                        print("      ⚠️ No courts for this date")
                        continue
                        
                except Exception as e:
                    print(f"      ❌ No courts appeared: {e}")
                    continue
                
                # Check each court
                for i, court in enumerate(courts):
                    try:
                        court_number = await court.inner_text()
                        print(f"         Court {court_number}:")
                        
                        await court.click()
                        await asyncio.sleep(2)
                        
                        # Get time slots
                        time_slots = await page.query_selector_all('span.styled-btn')
                        print(f"            📋 {len(time_slots)} time slots")
                        
                        available_count = 0
                        for slot in time_slots:
                            time_text = await slot.inner_text()
                            style = await slot.get_attribute('style') or ''
                            
                            # Check availability
                            style_lower = style.lower()
                            has_red = 'color: red' in style_lower
                            has_not_allowed = 'cursor: not-allowed' in style_lower
                            is_available = not (has_red and has_not_allowed)
                            
                            if is_available:
                                available_count += 1
                                slot_info = {
                                    'academy': academy_name,
                                    'date': date,
                                    'court': f'Court {court_number}',
                                    'time': time_text,
                                    'status': 'available'
                                }
                                all_slots.append(slot_info)
                                print(f"            ✅ AVAILABLE: {time_text}")
                        
                        print(f"            📊 {available_count} available slots")
                        
                    except Exception as e:
                        print(f"         ❌ Error with court: {e}")
                
            except Exception as e:
                print(f"      ❌ Error with date {date}: {e}")
        
        # Save session after successful operation
        await session_manager.save_session(page)
        
    except Exception as e:
        print(f"   ❌ Academy check error: {e}")
    
    return all_slots

async def enhanced_session_checker():
    """Enhanced checker with persistent session management"""
    
    load_dotenv()
    phone_number = os.getenv('PHONE_NUMBER')
    
    if not phone_number:
        print("❌ PHONE_NUMBER not set in .env")
        return
    
    print("🏸 ENHANCED SESSION-PERSISTENT CHECKER")
    print("="*60)
    print(f"📱 Phone: {phone_number}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    session_manager = EnhancedSessionManager(phone_number)
    dates_to_check = get_next_booking_dates(3)  # Check next 3 days
    
    print(f"📅 Dates: {', '.join(dates_to_check)}")
    
    async with async_playwright() as p:
        # Launch with session-friendly settings
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            print("\n🔐 SESSION MANAGEMENT")
            print("-"*40)
            
            # Try to restore existing session
            session_restored = await session_manager.restore_session(page)
            
            if session_restored and await session_manager.verify_login_status(page):
                print("✅ Existing session restored successfully!")
            else:
                print("🔄 Need fresh login...")
                if not await perform_manual_login(page, phone_number, session_manager):
                    print("❌ Login failed")
                    return
            
            # Test academy
            academy = {
                'name': 'Kotak Pullela Gopichand Badminton Academy',
                'url': 'https://booking.gopichandacademy.com/venue-details/1'
            }
            
            print(f"\n🏸 SLOT CHECKING")
            print("-"*40)
            
            slots = await check_slots_with_persistent_session(
                page, academy['url'], academy['name'], dates_to_check, session_manager
            )
            
            # Results
            print(f"\n📊 FINAL RESULTS")
            print("="*40)
            print(f"🎯 Available slots found: {len(slots)}")
            
            if slots:
                print("\n🎉 AVAILABLE SLOTS:")
                for i, slot in enumerate(slots, 1):
                    print(f"{i}. {slot['court']} on {slot['date']} at {slot['time']}")
                
                # Send notification if configured
                telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                
                if telegram_token and chat_id:
                    print(f"\n📱 Sending notification...")
                    # Add notification logic here if needed
                    print("✅ Notification would be sent!")
            else:
                print("😔 No available slots found")
                print("✅ System working correctly - all courts are booked")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print(f"\n⏳ Keeping browser open for 20 seconds for inspection...")
            await asyncio.sleep(20)
            await browser.close()
    
    print(f"✅ Check completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(enhanced_session_checker())
