#!/usr/bin/env python3
"""
GitHub Actions Badminton Checker
Simplified version that works with GitHub Actions automation
"""

import asyncio
import os
import sys
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.error("❌ Playwright not available")
    PLAYWRIGHT_AVAILABLE = False
    sys.exit(1)

class GitHubActionsChecker:
    """Simplified checker for GitHub Actions"""
    
    def __init__(self):
        # Get environment variables
        self.phone_number = os.getenv('PHONE_NUMBER')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.force_fresh_login = os.getenv('FORCE_FRESH_LOGIN', 'false').lower() == 'true'
        
        # Session files
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.cookies_file = self.data_dir / "github_cookies.json"
        self.session_file = self.data_dir / "github_session.json"
        
        # Academy configurations
        self.academies = [
            {
                'name': 'Kotak Pullela Gopichand Badminton Academy',
                'url': 'https://booking.gopichandacademy.com/venue-details/1',
                'short': 'Kotak'
            },
            {
                'name': 'Pullela Gopichand Badminton Academy',  
                'url': 'https://booking.gopichandacademy.com/venue-details/2',
                'short': 'Pullela'
            },
            {
                'name': 'SAI Pullela Gopichand National Badminton Academy',
                'url': 'https://booking.gopichandacademy.com/venue-details/3',
                'short': 'SAI'
            }
        ]
        
        # Validate required config
        missing_vars = []
        if not self.phone_number:
            missing_vars.append("PHONE_NUMBER")
        if not self.telegram_token:
            missing_vars.append("TELEGRAM_BOT_TOKEN") 
        if not self.chat_id:
            missing_vars.append("TELEGRAM_CHAT_ID")
            
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(f"❌ Startup failed: {error_msg}")
            
            # In GitHub Actions, provide helpful setup instructions
            if os.getenv('GITHUB_ACTIONS'):
                logger.error("🚨 GITHUB SECRETS SETUP REQUIRED:")
                logger.error(f"1. Go to: https://github.com/{os.getenv('GITHUB_REPOSITORY', 'YOUR_REPO')}/settings/secrets/actions")
                logger.error("2. Click 'New repository secret'")
                logger.error("3. Add these secrets:")
                for var in missing_vars:
                    if var == "PHONE_NUMBER":
                        logger.error(f"   • {var}: Your phone number with country code (e.g., +1234567890)")
                    elif var == "TELEGRAM_BOT_TOKEN":
                        logger.error(f"   • {var}: Get from @BotFather on Telegram")
                    elif var == "TELEGRAM_CHAT_ID":
                        logger.error(f"   • {var}: Get from @RawDataBot on Telegram")
                logger.error("")
                logger.error("For detailed instructions, see: GITHUB_ACTIONS_SETUP.md")
            
            raise ValueError(error_msg)
    
    def send_telegram_message(self, message):
        """Send message via Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram message sent successfully")
                return True
            else:
                logger.error(f"❌ Telegram send failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")
            return False

    async def wait_for_otp_reply(self, timeout_minutes=5):
        """Wait for OTP reply from user via Telegram"""
        try:
            # Get the latest message ID to know where to start checking
            url = f"https://api.telegram.org/bot{self.telegram_token}/getUpdates"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error("❌ Failed to get Telegram updates")
                return None
                
            updates = response.json().get('result', [])
            last_update_id = updates[-1]['update_id'] if updates else 0
            
            logger.info(f"⏳ Waiting for OTP reply (timeout: {timeout_minutes} minutes)...")
            start_time = datetime.now()
            timeout_seconds = timeout_minutes * 60
            
            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                # Check for new messages
                url = f"https://api.telegram.org/bot{self.telegram_token}/getUpdates"
                params = {'offset': last_update_id + 1, 'timeout': 10}
                
                try:
                    response = requests.get(url, params=params, timeout=15)
                    if response.status_code != 200:
                        continue
                        
                    updates = response.json().get('result', [])
                    
                    for update in updates:
                        if 'message' in update and 'text' in update['message']:
                            # Check if message is from the correct chat
                            if str(update['message']['chat']['id']) == str(self.chat_id):
                                message_text = update['message']['text'].strip()
                                
                                # Check if it looks like an OTP (4-6 digits)
                                if message_text.isdigit() and 4 <= len(message_text) <= 6:
                                    logger.info(f"✅ Received OTP: {message_text}")
                                    return message_text
                                
                        last_update_id = update['update_id']
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error checking for updates: {e}")
                    continue
                    
                # Small delay between checks
                await asyncio.sleep(2)
            
            logger.warning(f"⏰ OTP timeout after {timeout_minutes} minutes")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error waiting for OTP: {e}")
            return None
    
    def get_check_dates(self):
        """Get next upcoming Friday and Monday"""
        dates = []
        today = datetime.now()
        found_days = set()
        
        # Find the next upcoming Friday and Monday (one of each)
        for i in range(1, 15):
            check_date = today + timedelta(days=i)
            weekday = check_date.strftime('%A').lower()
            
            if weekday in ['friday', 'monday'] and weekday not in found_days:
                dates.append(check_date.strftime('%Y-%m-%d'))
                found_days.add(weekday)
                
                # Stop once we have both
                if len(found_days) == 2:
                    break
        
        return sorted(dates)
    
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
            
            logger.info(f"Session saved: {len(cookies)} cookies")
            return True
            
        except Exception as e:
            logger.error(f"Session save failed: {e}")
            return False
    
    async def restore_session(self, page):
        """Restore session state"""
        try:
            if not self.session_file.exists() or not self.cookies_file.exists():
                logger.info("No session data found")
                return False
            
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check session age (sessions expire after ~24 hours)
            session_time = datetime.fromisoformat(session_data['timestamp'])
            age_hours = (datetime.now() - session_time).total_seconds() / 3600
            
            if age_hours > 24:
                logger.info(f"Session too old ({age_hours:.1f} hours), need fresh login")
                return False
            
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            if cookies:
                await page.context.add_cookies(cookies)
                logger.info(f"Restored {len(cookies)} cookies")
            
            # Navigate to a test page
            await page.goto(session_data.get('url', 'https://booking.gopichandacademy.com/'), 
                           wait_until='networkidle', timeout=15000)
            await asyncio.sleep(3)
            
            # Restore local storage
            for key, value in session_data.get('local_storage', {}).items():
                try:
                    await page.evaluate(f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                except:
                    pass
            
            # Restore session storage
            for key, value in session_data.get('session_storage', {}).items():
                try:
                    await page.evaluate(f"sessionStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                except:
                    pass
            
            logger.info("Session restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Session restore failed: {e}")
            return False
    
    async def verify_login(self, page):
        """Check if we're logged in"""
        try:
            # Test access to a protected page
            await page.goto('https://booking.gopichandacademy.com/venue-details/1', 
                           wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(3)
            
            # If we're redirected to login, we're not authenticated
            if 'login' in page.url.lower():
                logger.info("Not logged in - redirected to login page")
                return False
            
            # Check for booking page elements
            date_input = await page.query_selector('input#card1[type="date"]')
            if date_input:
                logger.info("✅ Login verified - can access booking page")
                return True
            else:
                logger.info("❌ Login check failed - no booking elements found")
                return False
                
        except Exception as e:
            logger.error(f"Login verification failed: {e}")
            return False
    
    async def interactive_login(self, page):
        """Interactive login with OTP via Telegram"""
        try:
            logger.info("🔐 Starting interactive login process...")
            
            # Navigate to login page with increased timeout
            logger.info("🌐 Navigating to login page...")
            await page.goto('https://booking.gopichandacademy.com/login', 
                           wait_until='networkidle', timeout=30000)
            
            # Log page info after navigation
            title = await page.title()
            url = page.url
            logger.info(f"📄 Page loaded - Title: '{title}', URL: '{url}'")
            
            # Wait longer for dynamic content to load
            logger.info("⏳ Waiting for dynamic content to load...")
            await asyncio.sleep(10)
            
            # Check if there are any scripts or dynamic content loading
            scripts = await page.query_selector_all('script')
            logger.info(f"🔧 Found {len(scripts)} script tags on page")
            
            # Check for common loading indicators
            loading_indicators = ['loading', 'spinner', 'loader']
            for indicator in loading_indicators:
                elements = await page.query_selector_all(f'[class*="{indicator}"], [id*="{indicator}"]')
                if elements:
                    logger.info(f"🔄 Found loading indicator: {indicator}")
            
            # Try waiting for any input to appear
            logger.info("🔍 Waiting for any input element to appear...")
            try:
                await page.wait_for_selector('input', timeout=15000)
                logger.info("✅ Input element appeared after waiting")
            except Exception:
                logger.warning("⚠️ No input elements appeared after 15 seconds")
            
            # Check again after waiting
            all_inputs_after_wait = await page.query_selector_all('input')
            logger.info(f"📝 Found {len(all_inputs_after_wait)} input elements after waiting")
            
            # Check for iframes that might contain the login form
            iframes = await page.query_selector_all('iframe')
            logger.info(f"🖼️ Found {len(iframes)} iframe(s) on page")
            
            if iframes:
                for i, iframe in enumerate(iframes):
                    try:
                        frame = await iframe.content_frame()
                        if frame:
                            frame_inputs = await frame.query_selector_all('input')
                            logger.info(f"📝 Iframe #{i+1} contains {len(frame_inputs)} input elements")
                            if frame_inputs:
                                logger.info("🎯 Found inputs in iframe - switching context")
                                # Switch to this frame for further operations
                                page = frame
                                break
                    except Exception as e:
                        logger.info(f"⚠️ Could not access iframe #{i+1}: {e}")
            
            # Re-check for inputs in current context (main page or iframe)
            final_inputs = await page.query_selector_all('input')
            logger.info(f"📝 Final input count in current context: {len(final_inputs)}")
            
            # Find and fill phone number with multiple attempts
            logger.info("📱 Looking for phone input field...")
            phone_input = None
            phone_selectors = [
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="mobile"]',
                'input[name="phoneNumber"]',
                'input[placeholder*="phone" i]',
                'input[placeholder*="mobile" i]',
                'input[placeholder*="number" i]'
            ]
            
            for selector in phone_selectors:
                try:
                    phone_input = await page.wait_for_selector(selector, timeout=5000)
                    if phone_input:
                        logger.info(f"✅ Found phone input: {selector}")
                        break
                except Exception:
                    continue
            
            if not phone_input:
                logger.error("❌ Phone input field not found after trying all selectors")
                
                # Enhanced debugging - get page info
                try:
                    title = await page.title()
                    url = page.url
                    logger.error(f"📄 Current page - Title: '{title}', URL: '{url}'")
                    
                    # Check what inputs are actually available
                    all_inputs = await page.query_selector_all('input')
                    logger.error(f"📝 Found {len(all_inputs)} input elements on page:")
                    
                    for i, inp in enumerate(all_inputs[:10]):  # Limit to first 10
                        input_type = await inp.get_attribute('type') or 'no-type'
                        input_name = await inp.get_attribute('name') or 'no-name'
                        input_id = await inp.get_attribute('id') or 'no-id'
                        input_placeholder = await inp.get_attribute('placeholder') or 'no-placeholder'
                        logger.error(f"  Input #{i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
                    
                    # Save page content for analysis
                    page_content = await page.content()
                    with open('data/login_page_content.html', 'w', encoding='utf-8') as f:
                        f.write(page_content)
                    logger.error("💾 Page content saved to data/login_page_content.html")
                    
                except Exception as debug_e:
                    logger.error(f"Debug info collection failed: {debug_e}")
                
                # Take screenshot for debugging
                await page.screenshot(path='data/login_debug.png')
                logger.error("📸 Debug screenshot saved to data/login_debug.png")
                return False
                
            await phone_input.clear()
            # Remove +91 or other country codes as the site might add it automatically
            clean_phone = self.phone_number.replace('+91', '').replace('+', '').strip()
            await phone_input.fill(clean_phone)
            logger.info(f"📱 Phone number filled: {clean_phone}")
            await asyncio.sleep(2)
            
            # Find and click send OTP button with multiple attempts
            logger.info("🔍 Looking for Send OTP button...")
            send_otp_selectors = [
                'button:has-text("Send OTP")',
                'button:has-text("Get OTP")',
                'button:has-text("SEND OTP")',
                'button:has-text("Submit")',
                'button[type="submit"]',
                'input[type="submit"]',
                '.btn-primary',
                '.otp-button',
                'button.btn',
                '[role="button"]:has-text("OTP")',
                'a:has-text("Send")'
            ]
            
            otp_button = None
            for selector in send_otp_selectors:
                try:
                    otp_button = await page.wait_for_selector(selector, timeout=3000)
                    if otp_button:
                        # Check if button is visible and enabled
                        is_visible = await otp_button.is_visible()
                        is_enabled = await otp_button.is_enabled()
                        if is_visible and is_enabled:
                            logger.info(f"✅ Found OTP button: {selector}")
                            break
                        else:
                            logger.info(f"⚠️ Found button but not usable: {selector} (visible: {is_visible}, enabled: {is_enabled})")
                except Exception:
                    continue
            
            if not otp_button:
                logger.error("❌ Send OTP button not found")
                # Take screenshot for debugging
                await page.screenshot(path='data/otp_button_debug.png')
                return False
            
            # Click send OTP
            logger.info("📤 Clicking Send OTP button...")
            await otp_button.click()
            logger.info("📤 OTP request sent")
            await asyncio.sleep(5)  # Wait longer for OTP to be sent
            
            # Send Telegram message asking for OTP
            otp_request_message = (
                "🔐 *OTP Required for Badminton Checker*\n\n"
                f"📱 An OTP has been sent to your phone: `{clean_phone}`\n\n"
                "Please reply to this message with the OTP code (4-6 digits) within 5 minutes.\n\n"
                "Example: `123456`"
            )
            
            if not self.send_telegram_message(otp_request_message):
                logger.error("❌ Failed to send OTP request message")
                return False
            
            # Wait for OTP reply
            otp_code = await self.wait_for_otp_reply(timeout_minutes=5)
            if not otp_code:
                error_msg = (
                    "⏰ *OTP Timeout*\n\n"
                    "Did not receive OTP within 5 minutes.\n"
                    "The login attempt has failed.\n\n"
                    "I'll try again in the next hour."
                )
                self.send_telegram_message(error_msg)
                return False
            
            # Find OTP input field and enter the code with better detection
            logger.info("🔍 Looking for OTP input field...")
            otp_input_selectors = [
                'input[name="otp"]',
                'input[name="OTP"]',
                'input[placeholder*="OTP" i]',
                'input[placeholder*="code" i]',
                'input[placeholder*="verify" i]',
                'input[type="text"]:not([name="phone"]):not([name="mobile"])',
                'input[type="number"]:not([name="phone"]):not([name="mobile"])',
                'input.otp-input',
                'input#otp',
                'input[maxlength="6"]'
            ]
            
            otp_input = None
            for selector in otp_input_selectors:
                try:
                    otp_input = await page.wait_for_selector(selector, timeout=3000)
                    if otp_input:
                        is_visible = await otp_input.is_visible()
                        if is_visible:
                            logger.info(f"✅ Found OTP input: {selector}")
                            break
                        else:
                            logger.info(f"⚠️ Found hidden OTP input: {selector}")
                except Exception:
                    continue
            
            if not otp_input:
                logger.error("❌ OTP input field not found")
                # Take screenshot for debugging
                await page.screenshot(path='data/otp_input_debug.png')
                return False
            
            await otp_input.clear()
            await otp_input.fill(otp_code)
            logger.info(f"🔢 OTP entered: {otp_code}")
            await asyncio.sleep(2)
            
            # Find and click login/verify button with better detection
            logger.info("🔍 Looking for verify/login button...")
            login_selectors = [
                'button:has-text("Verify")',
                'button:has-text("VERIFY")',
                'button:has-text("Login")',
                'button:has-text("LOGIN")',
                'button:has-text("Submit")',
                'button:has-text("SUBMIT")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button.btn-verify',
                'button.verify-btn',
                '.btn-primary'
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = await page.wait_for_selector(selector, timeout=3000)
                    if login_button:
                        is_visible = await login_button.is_visible()
                        is_enabled = await login_button.is_enabled()
                        if is_visible and is_enabled:
                            logger.info(f"✅ Found login button: {selector}")
                            break
                        else:
                            logger.info(f"⚠️ Found unusable login button: {selector} (visible: {is_visible}, enabled: {is_enabled})")
                except Exception:
                    continue
            
            if not login_button:
                logger.error("❌ Login button not found")
                # Take screenshot for debugging
                await page.screenshot(path='data/login_button_debug.png')
                return False
            
            # Click login
            logger.info("🚀 Clicking verify/login button...")
            await login_button.click()
            logger.info("🚀 Login submitted")
            await asyncio.sleep(8)  # Wait longer for login to process
            
            # Check if login was successful
            logger.info(f"🔍 Current URL after login: {page.url}")
            if 'login' not in page.url.lower():
                logger.info("✅ Interactive login successful!")
                
                success_msg = (
                    "✅ *Login Successful!*\n\n"
                    "Your badminton slot checker is now logged in.\n"
                    "Continuing with slot checking...\n\n"
                    "🏸 I'll check for available slots now!"
                )
                self.send_telegram_message(success_msg)
                
                # Save the session
                await self.save_session(page)
                return True
            else:
                logger.error("❌ Login failed - still on login page")
                
                fail_msg = (
                    "❌ *Login Failed*\n\n"
                    "The OTP might be incorrect or expired.\n"
                    "I'll try again in the next hour.\n\n"
                    "Make sure to reply quickly with the correct OTP next time."
                )
                self.send_telegram_message(fail_msg)
                return False
                
        except Exception as e:
            logger.error(f"❌ Interactive login failed: {e}")
            error_msg = (
                "❌ *Login Error*\n\n"
                f"An error occurred during login: {str(e)}\n\n"
                "I'll try again in the next hour."
            )
            self.send_telegram_message(error_msg)
            return False
    
    async def check_academy_slots(self, page, academy, dates):
        """Check slots for one academy"""
        logger.info(f"🏸 Checking: {academy['name']}")
        all_slots = []
        
        try:
            # Navigate to academy page
            await page.goto(academy['url'], wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(4)
            
            # Check if we got redirected to login
            if 'login' in page.url.lower():
                logger.error("❌ Redirected to login - session expired")
                return []
            
            # Look for date input
            date_input = await page.query_selector('input#card1[type="date"]')
            if not date_input:
                logger.error("❌ Date input not found")
                return []
            
            # Check each date
            for date in dates:
                logger.info(f"   📅 Checking {date}")
                
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
                        logger.info(f"      No courts available for {date}")
                        continue
                    
                    logger.info(f"      Found {len(courts)} courts")
                    
                    # Check each court
                    for court in courts:
                        try:
                            court_name = await court.inner_text()
                            await court.click()
                            await asyncio.sleep(3)
                            
                            # Get time slots
                            time_slots = await page.query_selector_all('span.styled-btn')
                            available_count = 0
                            
                            for slot in time_slots:
                                try:
                                    time_text = await slot.inner_text()
                                    style = await slot.get_attribute('style') or ''
                                    
                                    # Check if slot is available (not red/disabled)
                                    is_booked = ('color: red' in style.lower() and 
                                               'cursor: not-allowed' in style.lower())
                                    
                                    if not is_booked:
                                        available_count += 1
                                        slot_info = {
                                            'academy': academy['short'],
                                            'academy_full': academy['name'],
                                            'date': date,
                                            'court': court_name,
                                            'time': time_text,
                                            'status': 'available'
                                        }
                                        all_slots.append(slot_info)
                                
                                except Exception:
                                    continue
                            
                            if available_count > 0:
                                logger.info(f"         ✅ {court_name}: {available_count} slots available")
                        
                        except Exception:
                            continue
                
                except Exception as e:
                    logger.error(f"      Error checking date {date}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Academy check failed: {e}")
        
        return all_slots
    
    def format_results_message(self, all_slots, dates):
        """Format results for Telegram"""
        if not all_slots:
            date_strs = [datetime.strptime(d, '%Y-%m-%d').strftime('%A %b %d') for d in dates]
            return (
                f"🏸 *Badminton Checker Update*\n\n"
                f"😔 No slots available\n\n"
                f"📅 Checked: {' & '.join(date_strs)}\n"
                f"🏟️ All 3 academies checked\n"
                f"⏰ Next check in 1 hour\n\n"
                f"All courts are currently booked."
            )
        
        # Group results
        slots_by_date = {}
        for slot in all_slots:
            date = slot['date']
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(slot)
        
        message = f"🏸 *SLOTS AVAILABLE!*\n\n"
        message += f"🎯 Found {len(all_slots)} available slots!\n\n"
        
        for date, slots in sorted(slots_by_date.items()):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d')
            message += f"📅 *{formatted_date}*\n"
            
            # Group by academy
            by_academy = {}
            for slot in slots:
                academy = slot['academy']
                if academy not in by_academy:
                    by_academy[academy] = []
                by_academy[academy].append(f"{slot['court']} at {slot['time']}")
            
            for academy, slot_list in by_academy.items():
                message += f"   🏟️ *{academy}*\n"
                for slot_detail in slot_list:
                    message += f"      🏸 {slot_detail}\n"
            
            message += "\n"
        
        message += "🔗 [Book Now](https://booking.gopichandacademy.com/)\n"
        message += f"⏰ Checked at {datetime.now().strftime('%H:%M IST')}"
        
        return message
    
    async def run_check(self):
        """Main checking logic"""
        logger.info("🏸 Starting badminton slot check...")
        
        dates = self.get_check_dates()
        date_strs = [datetime.strptime(d, '%Y-%m-%d').strftime('%A %b %d') for d in dates]
        logger.info(f"📅 Checking dates: {' & '.join(date_strs)}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-timeout',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 720}
            )
            
            # Set longer default timeouts
            context.set_default_timeout(60000)  # 60 seconds
            context.set_default_navigation_timeout(60000)  # 60 seconds
            
            page = await context.new_page()
            
            try:
                # Try to restore session unless forced fresh login
                session_restored = False
                if not self.force_fresh_login:
                    session_restored = await self.restore_session(page)
                
                # Verify login
                if session_restored:
                    logged_in = await self.verify_login(page)
                else:
                    logged_in = False
                
                if not logged_in:
                    logger.warning("❌ Not logged in - attempting interactive login")
                    
                    # Try interactive login
                    login_success = await self.interactive_login(page)
                    if not login_success:
                        logger.error("❌ Interactive login failed")
                        return
                    
                    logger.info("✅ Interactive login successful, proceeding...")
                else:
                    logger.info("✅ Already logged in, proceeding with checks...")
                
                # Check all academies
                all_available_slots = []
                for academy in self.academies:
                    slots = await self.check_academy_slots(page, academy, dates)
                    all_available_slots.extend(slots)
                    
                    if slots:
                        logger.info(f"✅ {academy['short']}: {len(slots)} slots found")
                    else:
                        logger.info(f"😔 {academy['short']}: No slots available")
                
                # Save session for next run
                await self.save_session(page)
                
                # Send results
                message = self.format_results_message(all_available_slots, dates)
                self.send_telegram_message(message)
                
                logger.info(f"🎯 Total slots found: {len(all_available_slots)}")
                logger.info("✅ Check completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Check failed: {e}")
                self.send_telegram_message(
                    f"❌ *Badminton Checker Error*\n\n"
                    f"Error: `{str(e)[:100]}`\n\n"
                    f"Will try again in the next hour."
                )
                
            finally:
                await browser.close()

async def main():
    """Main entry point"""
    try:
        checker = GitHubActionsChecker()
        await checker.run_check()
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
