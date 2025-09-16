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

# Load environment variables from .env file if running locally
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent / '.env'
    
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Set environment variable only if not already set
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"Warning: Failed to load .env file: {e}")

# Load .env file on import
load_env_file()

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
            # Detect environment for adaptive behavior
            is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
            is_headless = os.getenv('CI') == 'true' or is_github_actions
            
            logger.info("🔐 Starting interactive login process...")
            if is_github_actions:
                logger.info("🤖 Running in GitHub Actions environment - using enhanced compatibility mode")
            elif is_headless:
                logger.info("🖥️ Running in headless CI environment")
            else:
                logger.info("💻 Running in local environment")
            
            # Navigate to main SPA page first (since /login returns 404)
            logger.info("🌐 Navigating to main SPA page...")
            
            # Use longer timeouts for GitHub Actions
            nav_timeout = 45000 if is_github_actions else 30000
            
            await page.goto('https://booking.gopichandacademy.com/', 
                           wait_until='networkidle', timeout=nav_timeout)
            
            # Log page info after navigation
            title = await page.title()
            url = page.url
            logger.info(f"📄 Page loaded - Title: '{title}', URL: '{url}'")
            
            # Wait longer for dynamic content to load
            logger.info("⏳ Waiting for React SPA to initialize...")
            await asyncio.sleep(10)
            
            # Check if there are any scripts or dynamic content loading
            scripts = await page.query_selector_all('script')
            logger.info(f"🔧 Found {len(scripts)} script tags on page")
            
            # Find and click the "Login / SignUp" button to open the modal
            logger.info("🔍 Looking for 'Login / SignUp' button...")
            login_found = False
            
            # The specific selector for the Login/SignUp button based on the HTML
            login_btn_selectors = [
                '.login-btn',
                '[class*="login-btn"]',
                'div:has-text("Login / ")',
                'div:has-text("SignUp")',
                'span:has-text("Login /")',
            ]
            
            for selector in login_btn_selectors:
                try:
                    login_element = await page.query_selector(selector)
                    if login_element:
                        logger.info(f"🎯 Found login button with selector: {selector}")
                        
                        # Click the login button to open modal
                        await login_element.click()
                        logger.info("� Clicked login button - modal should appear")
                        
                        # Wait for modal to appear
                        await asyncio.sleep(3)
                        
                        # Check if modal appeared by looking for modal-overlay
                        modal = await page.query_selector('.modal-overlay')
                        if modal:
                            logger.info("✅ Login modal appeared!")
                            
                            # DEBUGGING: Take screenshot of modal that appeared
                            await page.screenshot(path='data/debug_modal_appeared.png')
                            logger.info("📸 Debug: Screenshot saved - modal_appeared.png")
                            
                            # Check if we got the Register modal instead of Login modal
                            # Look for "Register" title or "Login to your account" link
                            try:
                                # Save modal HTML content for debugging
                                modal_html = await modal.inner_html()
                                with open('data/debug_modal_content.html', 'w', encoding='utf-8') as f:
                                    f.write(modal_html)
                                logger.info("💾 Debug: Modal HTML saved - modal_content.html")
                                
                                # Check if this is the register modal
                                register_title = await modal.query_selector('text="Register"')
                                login_link = await modal.query_selector('text="Login to your account"')
                                
                                # Also check for register-specific elements
                                name_field = await modal.query_selector('input[placeholder*="Name" i]')
                                email_field = await modal.query_selector('input[placeholder*="Email" i]')
                                
                                logger.info(f"🔍 Modal analysis:")
                                logger.info(f"   Register title found: {register_title is not None}")
                                logger.info(f"   Login link found: {login_link is not None}")
                                logger.info(f"   Name field found: {name_field is not None}")
                                logger.info(f"   Email field found: {email_field is not None}")
                                
                                if register_title and login_link:
                                    logger.info("📝 Register modal detected - need to switch to login")
                                    logger.info("🔗 Clicking 'Login to your account' link...")
                                    
                                    # Take screenshot before clicking login link
                                    await page.screenshot(path='data/debug_before_login_click.png')
                                    logger.info("📸 Debug: Before clicking login link")
                                    
                                    # Click the "Login to your account" red link
                                    await login_link.click()
                                    await asyncio.sleep(3)
                                    
                                    # Take screenshot after clicking login link
                                    await page.screenshot(path='data/debug_after_login_click.png')
                                    logger.info("📸 Debug: After clicking login link")
                                    
                                    logger.info("✅ Switched to login modal")
                                    
                                elif register_title or name_field or email_field:
                                    # This is likely a register modal, try alternative selectors for the login link
                                    logger.info("📝 Register modal detected - looking for login link with alternative selectors...")
                                    
                                    login_link_selectors = [
                                        'text="Login to your account"',
                                        'a:has-text("Login to your account")',
                                        '[style*="color: red"]:has-text("Login")',
                                        '.text-red:has-text("Login")',
                                        'a[href*="login"]',
                                        '*:has-text("Login to your account")',
                                        'a[style*="color"]',
                                        '.login-link'
                                    ]
                                    
                                    link_clicked = False
                                    for selector in login_link_selectors:
                                        try:
                                            link = await modal.query_selector(selector)
                                            if link:
                                                logger.info(f"🔗 Found login link with selector: {selector}")
                                                
                                                # Take screenshot before click
                                                safe_selector = selector.replace(":", "_").replace("*", "_").replace('"', "")[:10]
                                                await page.screenshot(path=f'data/debug_before_link_{safe_selector}.png')
                                                
                                                await link.click()
                                                await asyncio.sleep(3)
                                                
                                                # Take screenshot after click
                                                await page.screenshot(path=f'data/debug_after_link_{safe_selector}.png')
                                                
                                                logger.info("✅ Switched to login modal")
                                                link_clicked = True
                                                break
                                        except Exception as e:
                                            logger.debug(f"Login link selector {selector} failed: {e}")
                                    
                                    if not link_clicked:
                                        logger.warning("⚠️ Could not find 'Login to your account' link")
                                        # Take screenshot for debugging
                                        await page.screenshot(path='data/debug_register_modal_no_link.png')
                                        logger.info("📸 Debug: Register modal but no login link found")
                                        
                                        # Log all clickable elements in modal for debugging
                                        links = await modal.query_selector_all('a, button, [onclick], [style*="cursor"]')
                                        logger.info(f"🔍 Found {len(links)} clickable elements in modal:")
                                        for i, link in enumerate(links[:10]):  # Limit to first 10
                                            try:
                                                text = await link.inner_text()
                                                tag = await link.evaluate('el => el.tagName')
                                                logger.info(f"   Clickable {i+1}: {tag} - '{text[:50]}'")
                                            except:
                                                pass
                                else:
                                    logger.info("✅ Login modal is already showing (not register modal)")
                                    # Take screenshot to confirm
                                    await page.screenshot(path='data/debug_login_modal_confirmed.png')
                                    logger.info("📸 Debug: Confirmed login modal")
                                    
                            except Exception as e:
                                logger.debug(f"Modal type detection failed: {e}")
                                logger.info("🤷 Proceeding with assumption this is login modal")
                                await page.screenshot(path='data/debug_modal_detection_error.png')
                                logger.info("📸 Debug: Modal detection error")
                            
                            login_found = True
                            break
                        else:
                            logger.info("⚠️ Modal didn't appear, trying other selectors...")
                            
                except Exception as e:
                    logger.debug(f"⚠️ Selector {selector} failed: {e}")
            
            # If still not found, try clicking any element containing "Login" text
            if not login_found:
                logger.info("🔄 Trying to find any element with Login text...")
                try:
                    # Use more specific text matching
                    await page.click('text=Login / SignUp', timeout=5000)
                    logger.info("� Clicked 'Login / SignUp' text")
                    await asyncio.sleep(3)
                    
                    modal = await page.query_selector('.modal-overlay')
                    if modal:
                        logger.info("✅ Login modal appeared after text click!")
                        login_found = True
                except Exception as e:
                    logger.debug(f"⚠️ Text click failed: {e}")
            
            # Alternative: try clicking the header area where the login button should be
            if not login_found:
                logger.info("🔄 Trying header area click...")
                try:
                    header = await page.query_selector('header.header-section')
                    if header:
                        # Look for any clickable element in header containing login-related text
                        login_elements = await header.query_selector_all('div, span')
                        for element in login_elements:
                            text = await element.inner_text()
                            if 'Login' in text or 'SignUp' in text:
                                logger.info(f"🎯 Found login element in header: '{text}'")
                                await element.click()
                                await asyncio.sleep(3)
                                
                                modal = await page.query_selector('.modal-overlay')
                                if modal:
                                    logger.info("✅ Login modal appeared after header click!")
                                    login_found = True
                                    break
                except Exception as e:
                    logger.debug(f"⚠️ Header click failed: {e}")
            
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
            
            # Log current URL after all attempts
            current_url = page.url
            logger.info(f"📍 Current URL after login attempts: {current_url}")
            # Now that modal is open, look for phone input field specifically within the modal
            logger.info("📱 Looking for phone input field within the modal...")
            phone_input = None
            
            # First, ensure we're working within the modal context
            modal = await page.query_selector('.modal-overlay')
            if not modal:
                logger.error("❌ Modal overlay not found - cannot proceed with login")
                await page.screenshot(path='data/modal_not_found.png')
                return False
            
            logger.info("✅ Modal overlay found, looking for form elements...")
            
            # Based on the HTML structure, the phone input has specific attributes
            modal_phone_selectors = [
                '.modal-overlay input[id="mobile"]',  # Based on the HTML: <input ... id="mobile">
                '.modal-overlay input[placeholder*="Mobile Number" i]',  # Placeholder: "Enter Your Mobile Number"
                '.modal-overlay input[type="text"]',  # It's type="text" not "tel"
                '.modal-overlay input[maxlength="10"]',  # Has maxlength="10"
                '.modal-content input[id="mobile"]',
                '.modal-content input',
                '.contact-form input[id="mobile"]',
                '.contact-form input',
                'form input[id="mobile"]',
                'input[id="mobile"]'  # Fallback to just the ID
            ]
            
            for selector in modal_phone_selectors:
                try:
                    phone_input = await page.wait_for_selector(selector, timeout=5000)
                    if phone_input:
                        logger.info(f"✅ Found phone input in modal: {selector}")
                        
                        # Verify it's the right input by checking attributes
                        input_id = await phone_input.get_attribute('id')
                        input_placeholder = await phone_input.get_attribute('placeholder')
                        input_type = await phone_input.get_attribute('type')
                        input_maxlength = await phone_input.get_attribute('maxlength')
                        
                        logger.info(f"📝 Input details - ID: '{input_id}', Placeholder: '{input_placeholder}', Type: '{input_type}', MaxLength: '{input_maxlength}'")
                        break
                        
                except Exception as e:
                    logger.debug(f"⚠️ Modal selector {selector} failed: {e}")
                    continue
            
            if not phone_input:
                logger.error("❌ Phone input field not found within modal")
                
                # Enhanced debugging - check what's in the modal
                try:
                    modal_content = await modal.inner_html()
                    logger.error("🔍 Modal content analysis:")
                    
                    # Look for all inputs in modal
                    modal_inputs = await modal.query_selector_all('input')
                    logger.error(f"📝 Found {len(modal_inputs)} input elements in modal:")
                    
                    for i, inp in enumerate(modal_inputs):
                        input_type = await inp.get_attribute('type') or 'no-type'
                        input_name = await inp.get_attribute('name') or 'no-name'
                        input_id = await inp.get_attribute('id') or 'no-id'
                        input_placeholder = await inp.get_attribute('placeholder') or 'no-placeholder'
                        input_class = await inp.get_attribute('class') or 'no-class'
                        logger.error(f"  Modal Input #{i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}', class='{input_class}'")
                    
                    # Save modal content for analysis
                    with open('data/modal_content.html', 'w', encoding='utf-8') as f:
                        f.write(modal_content)
                    logger.error("💾 Modal content saved to data/modal_content.html")
                    
                except Exception as debug_e:
                    logger.error(f"Modal debug info collection failed: {debug_e}")
                
                # Take screenshot for debugging
                await page.screenshot(path='data/modal_debug.png')
                logger.error("📸 Debug screenshot saved to data/modal_debug.png")
                return False
            
            if not phone_input:
                logger.error("❌ Phone input field not found within modal")
                
                # Enhanced debugging - check what's in the modal
                try:
                    modal_content = await modal.inner_html()
                    logger.error("� Modal content analysis:")
                    
                    # Look for all inputs in modal
                    modal_inputs = await modal.query_selector_all('input')
                    logger.error(f"📝 Found {len(modal_inputs)} input elements in modal:")
                    
                    for i, inp in enumerate(modal_inputs):
                        input_type = await inp.get_attribute('type') or 'no-type'
                        input_name = await inp.get_attribute('name') or 'no-name'
                        input_id = await inp.get_attribute('id') or 'no-id'
                        input_placeholder = await inp.get_attribute('placeholder') or 'no-placeholder'
                        input_class = await inp.get_attribute('class') or 'no-class'
                        logger.error(f"  Modal Input #{i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}', class='{input_class}'")
                    
                    # Save modal content for analysis
                    with open('data/modal_content.html', 'w', encoding='utf-8') as f:
                        f.write(modal_content)
                    logger.error("💾 Modal content saved to data/modal_content.html")
                    
                except Exception as debug_e:
                    logger.error(f"Modal debug info collection failed: {debug_e}")
                
                # Take screenshot for debugging
                await page.screenshot(path='data/modal_debug.png')
                logger.error("📸 Debug screenshot saved to data/modal_debug.png")
                return False
            
            # Clear and fill the phone input
            await phone_input.fill("")  # Clear by filling with empty string
            # Remove +91 or other country codes as the site might add it automatically
            clean_phone = self.phone_number.replace('+91', '').replace('+', '').strip()
            await phone_input.fill(clean_phone)
            logger.info(f"📱 Phone number filled: {clean_phone}")
            
            # Verify the phone number was actually filled
            await asyncio.sleep(1)
            actual_value = await phone_input.input_value()
            if actual_value != clean_phone:
                logger.warning(f"⚠️ Phone input verification failed. Expected: {clean_phone}, Actual: {actual_value}")
                # Try filling again
                await phone_input.fill("")
                await asyncio.sleep(0.5)
                await phone_input.fill(clean_phone)
                await asyncio.sleep(1)
                actual_value = await phone_input.input_value()
                logger.info(f"📱 Phone number re-filled. Final value: {actual_value}")
            
            # DEBUGGING: Take screenshot after phone filling to see current modal state
            await page.screenshot(path='data/debug_after_phone_fill.png')
            logger.info("📸 Debug: After phone number filling")
            
            await asyncio.sleep(2)
            
            # Find and click send OTP button within the modal
            logger.info("🔍 Looking for Send OTP button in modal...")
            
            # Based on the HTML, the button has class="custom-button" and value="Send OTP"
            modal_otp_selectors = [
                '.modal-overlay .custom-button',  # The class that actually exists (from debug)
                '.modal-overlay input[type="submit"]',  # Generic submit button in modal
                '.modal-overlay input[value="Send OTP"]',  # Specific to the HTML structure
                '.modal-content .custom-button',
                '.modal-content input[type="submit"]',
                '.contact-form input[type="submit"]',
                '.contact-form .custom-button',
                'form input[value="Send OTP"]',
                'form .custom-button',
                '.modal-overlay button',  # Fallback to any button in modal
                '.modal-content button'   # Fallback to any button in modal content
            ]
            
            otp_button = None
            for selector in modal_otp_selectors:
                try:
                    # Use longer timeout for GitHub Actions environment
                    selector_timeout = 10000 if is_github_actions else 5000
                    otp_button = await page.wait_for_selector(selector, timeout=selector_timeout)
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
            
            # Click send OTP with multiple strategies
            logger.info("📤 Clicking Send OTP button...")
            
            # DEBUGGING: Take screenshot before OTP button click
            await page.screenshot(path='data/debug_before_otp_click.png')
            logger.info("📸 Debug: Before OTP button click")
            
            try:
                # Strategy 1: Regular click with reduced timeout
                logger.info("🔄 Attempting regular click...")
                await otp_button.click(timeout=10000)
                logger.info("✅ Regular click completed")
                
                # Wait a bit and check for immediate feedback
                await asyncio.sleep(2)
                
            except Exception as regular_click_error:
                logger.warning(f"⚠️ Regular click failed: {regular_click_error}")
                
                try:
                    # Strategy 2: JavaScript click (more reliable in headless environments)
                    logger.info("� Attempting JavaScript click...")
                    await otp_button.evaluate('element => element.click()')
                    logger.info("✅ JavaScript click completed")
                    await asyncio.sleep(2)
                    
                except Exception as js_click_error:
                    logger.warning(f"⚠️ JavaScript click failed: {js_click_error}")
                    
                    try:
                        # Strategy 3: Form submission via JavaScript
                        logger.info("🔄 Attempting form submission...")
                        form_submit_result = await modal.evaluate("""
                            () => {
                                const form = document.querySelector('form.contact-form');
                                if (form) {
                                    form.submit();
                                    return 'form_submitted';
                                }
                                return 'no_form_found';
                            }
                        """)
                        logger.info(f"📋 Form submission result: {form_submit_result}")
                        await asyncio.sleep(2)
                        
                    except Exception as form_submit_error:
                        logger.warning(f"⚠️ Form submission failed: {form_submit_error}")
                        
                        try:
                            # Strategy 4: Dispatch click event
                            logger.info("🔄 Attempting event dispatch...")
                            await otp_button.evaluate("""
                                element => {
                                    const event = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    element.dispatchEvent(event);
                                }
                            """)
                            logger.info("✅ Event dispatch completed")
                            await asyncio.sleep(2)
                            
                        except Exception as dispatch_error:
                            logger.error(f"❌ All click strategies failed. Last error: {dispatch_error}")
                            await page.screenshot(path='data/otp_click_error.png')
                            return False
            
            # DEBUGGING: Take screenshot after OTP button click
            await page.screenshot(path='data/debug_after_otp_click.png')
            logger.info("📸 Debug: After OTP button click")
            
            # Enhanced check for OTP request success with longer timeout for different environments
            logger.info("🔍 Checking for OTP request confirmation...")
            
            # Strategy 1: Look for immediate UI changes (fast check)
            otp_sent = False
            for indicator in ['text="OTP sent"', 'text="Code sent"', 'text="Sent"']:
                try:
                    element = await page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        logger.info(f"✅ Found OTP confirmation: {indicator}")
                        otp_sent = True
                        break
                except:
                    continue
            
            if not otp_sent:
                # Strategy 2: Check for OTP input fields appearing (medium check)
                logger.info("🔍 Checking for OTP input field appearance...")
                otp_input_selectors = [
                    'input[placeholder*="OTP" i]',
                    'input[placeholder*="code" i]',
                    'input[placeholder*="verify" i]',
                    'input[maxlength="4"]',
                    'input[maxlength="6"]',
                    '.otp-input'
                ]
                
                for selector in otp_input_selectors:
                    try:
                        otp_input_field = await page.wait_for_selector(selector, timeout=3000)
                        if otp_input_field and await otp_input_field.is_visible():
                            logger.info(f"✅ OTP input field appeared: {selector}")
                            otp_sent = True
                            break
                    except:
                        continue
            
            if not otp_sent:
                # Strategy 3: Check for network activity or form changes (slower check)
                logger.info("🔍 Checking for page changes after button click...")
                try:
                    # Check if the phone input became readonly (common pattern after OTP send)
                    phone_readonly = await phone_input.evaluate('element => element.readOnly')
                    phone_disabled = await phone_input.evaluate('element => element.disabled')
                    
                    if phone_readonly or phone_disabled:
                        logger.info(f"✅ Phone input state changed (readonly: {phone_readonly}, disabled: {phone_disabled})")
                        otp_sent = True
                    else:
                        # Check for button state changes
                        button_text = await otp_button.evaluate('element => element.value || element.textContent')
                        if 'resend' in button_text.lower() or 'sent' in button_text.lower():
                            logger.info(f"✅ Button text changed to: {button_text}")
                            otp_sent = True
                        else:
                            # Final check: assume success if no errors occurred during clicking
                            logger.info("ℹ️ No explicit confirmation found, but clicks succeeded")
                            logger.info("🤞 Assuming OTP was sent successfully (GitHub Actions compatibility mode)")
                            otp_sent = True
                            
                except Exception as state_check_error:
                    logger.info(f"⚠️ State check failed: {state_check_error}")
                    logger.info("🤞 Assuming OTP was sent (fallback for GitHub Actions)")
                    otp_sent = True
            
            if otp_sent:
                logger.info("📤 OTP request confirmed - proceeding to wait for code")
            else:
                logger.error("❌ Could not confirm OTP was sent")
                await page.screenshot(path='data/otp_send_failed.png')
                return False
            
            # Send Telegram message asking for OTP with environment-aware timeout
            timeout_minutes = 10 if is_github_actions else 5  # Longer timeout for GitHub Actions
            
            otp_request_message = (
                "🔐 *OTP Required for Badminton Checker*\n\n"
                f"📱 An OTP has been sent to your phone: `{clean_phone}`\n\n"
                f"Please reply to this message with the OTP code (4-6 digits) within {timeout_minutes} minutes.\n\n"
                "Example: `123456`"
            )
            
            if is_github_actions:
                otp_request_message += "\n\n🤖 _Running in GitHub Actions - please respond promptly_"
            
            if not self.send_telegram_message(otp_request_message):
                logger.error("❌ Failed to send OTP request message")
                return False
            
            # Wait for OTP reply with environment-specific timeout
            otp_code = await self.wait_for_otp_reply(timeout_minutes=timeout_minutes)
            if not otp_code:
                error_msg = (
                    f"⏰ *OTP Timeout*\n\n"
                    f"Did not receive OTP within {timeout_minutes} minutes.\n"
                    "The login attempt has failed.\n\n"
                    "I'll try again in the next hour."
                )
                if is_github_actions:
                    error_msg += "\n\n🤖 _GitHub Actions environment may require faster response times_"
                
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
            input_timeout = 8000 if is_github_actions else 3000
            
            for selector in otp_input_selectors:
                try:
                    otp_input = await page.wait_for_selector(selector, timeout=input_timeout)
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
            
            await otp_input.fill("")  # Clear any existing content
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
            button_timeout = 8000 if is_github_actions else 3000
            
            for selector in login_selectors:
                try:
                    login_button = await page.wait_for_selector(selector, timeout=button_timeout)
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
            
            # Click login with multiple strategies (similar to OTP button)
            logger.info("🚀 Clicking verify/login button...")
            
            try:
                await login_button.click(timeout=5000)
                logger.info("✅ Login button clicked successfully")
            except Exception as click_error:
                logger.warning(f"⚠️ Regular click failed: {click_error}")
                try:
                    # Fallback to JavaScript click
                    await login_button.evaluate('element => element.click()')
                    logger.info("✅ Login button clicked via JavaScript")
                except Exception as js_error:
                    logger.error(f"❌ All login button click strategies failed: {js_error}")
                    return False
            
            logger.info("🚀 Login submitted")
            
            # Wait longer for login processing in GitHub Actions
            processing_wait = 12 if is_github_actions else 8
            await asyncio.sleep(processing_wait)
            
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
        """Format results for Telegram with table format"""
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
        
        # Group results by date
        slots_by_date = {}
        for slot in all_slots:
            date = slot['date']
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(slot)
        
        # Determine if we have any slots at all
        has_any_slots = len(all_slots) > 0
        
        if has_any_slots:
            message = f"🏸 *SLOTS AVAILABLE!*\n\n"
            message += f"🎯 Found {len(all_slots)} available slots!\n\n"
            message += f"*Legend:* ✓ = Available, ✗ = Booked\n\n"
        else:
            message = f"🏸 *Badminton Checker Update*\n\n"
            message += f"😔 No slots available\n\n"
        
        # Check each date (both those with and without slots)
        for date in sorted(dates):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d')
            message += f"📅 *{formatted_date}*\n\n"
            
            if date in slots_by_date:
                # This date has slots - create tables for each academy
                slots = slots_by_date[date]
                
                # Group by academy
                by_academy = {}
                for slot in slots:
                    academy = slot['academy']
                    if academy not in by_academy:
                        by_academy[academy] = []
                    by_academy[academy].append(slot)
                
                # Create table for each academy
                for academy_short in ['Kotak', 'Pullela', 'SAI']:  # Process in this order
                    if academy_short in by_academy:
                        message += self.create_academy_table(academy_short, by_academy[academy_short])
                        message += "\n"
            else:
                # This date has no slots
                message += f"😔 No slots available for this date\n\n"
        
        message += "🔗 [Book Now](https://booking.gopichandacademy.com/)\n"
        message += f"⏰ Checked at {datetime.now().strftime('%H:%M IST')}"
        
        return message
    
    def create_academy_table(self, academy_short, academy_slots):
        """Create a compact table format for an academy's available slots"""
        # Define academy-specific configurations based on actual data patterns
        academy_configs = {
            'Kotak': {
                'courts': list(range(1, 7)),  # Courts 1-6
                'time_slots': ['12:00-13:00', '13:00-14:00', '18:00-19:00', '19:00-20:00', '20:00-21:00', '21:00-22:00'],
                'time_labels': ['12h', '13h', '18h', '19h', '20h', '21h']  # Compact labels
            },
            'Pullela': {
                'courts': list(range(1, 9)),  # Courts 1-8 
                'time_slots': ['12:00-13:00', '13:00-14:00', '19:00-20:00', '20:00-21:00', '21:00-22:00'],
                'time_labels': ['12h', '13h', '19h', '20h', '21h']
            },
            'SAI': {
                'courts': list(range(1, 10)),  # Courts 1-9
                'time_slots': ['12:00-13:00', '13:00-14:00', '19:00-20:00', '20:00-21:00', '21:00-22:00'],
                'time_labels': ['12h', '13h', '19h', '20h', '21h']
            }
        }
        
        config = academy_configs.get(academy_short, {})
        courts = config.get('courts', [])
        time_slots = config.get('time_slots', [])
        time_labels = config.get('time_labels', [])
        
        # Create set of available court-time combinations
        available_slots = set()
        for slot in academy_slots:
            court_num = slot['court'].strip()
            time = slot['time'].strip()
            # Extract just the number from court (in case it's "Court 1" or "1")
            court_number = ''.join(filter(str.isdigit, court_num))
            if court_number:
                available_slots.add((int(court_number), time))
        
        # Build compact table using shorter format
        table_text = f"🏟️ *{academy_short}*\n"
        
        # Use a more compact format with fixed-width cells
        table_text += "`C "  # Court column header (shortened)
        for label in time_labels:
            table_text += f"{label:>4}"  # 4 characters per time slot
        table_text += "`\n"
        
        # Separator line
        table_text += "`" + "-" * (2 + len(time_labels) * 4) + "`\n"
        
        # Rows for each court (more compact)
        for court in courts:
            table_text += f"`{court} "
            for i, time_slot in enumerate(time_slots):
                if (court, time_slot) in available_slots:
                    table_text += f"{'✓':>4}"  # Available
                else:
                    table_text += f"{'✗':>4}"  # Not available
            table_text += "`\n"
        
        return table_text
    
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
