import asyncio
import logging
import os
import json
from typing import Optional, Any

try:
    from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    # Fallback for when playwright is not installed
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeoutError = TimeoutError

class LoginHandler:
    """
    Handles authentication with the badminton booking website
    """
    
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.login_url = "https://booking.gopichandacademy.com/"
        self.session_file = "data/session.json"
        self.cookies_file = "data/cookies.json"
        
        # Login selectors - updated for modern SPA
        self.selectors = {
            "phone_input": "input[type='tel'], input[name*='phone'], input[placeholder*='phone'], input[placeholder*='mobile'], input[placeholder*='number']",
            "send_otp_button": "input[type='submit'].custom-button, button:has-text('Send OTP'), button:has-text('Send'), button:has-text('Get OTP'), button[type='submit'], .custom-button",
            "otp_input": "input[type='text'][maxlength='6'], input[placeholder*='OTP'], input[name*='otp'], input[placeholder*='verification']",
            "verify_button": "button:has-text('Verify'), button:has-text('Submit'), button:has-text('Login'), button[type='submit']",
            "login_form": "form, .login-form, .auth-form, [class*='login'], [class*='auth']"
        }
        
    async def login(self, page: Any) -> bool:
        """
        Handle complete login flow with phone number and OTP for SPA websites
        """
        try:
            # Try to restore session first
            if await self._restore_session(page):
                logging.info("Session restored successfully")
                if await self._verify_login_status(page):
                    return True
            
            # Navigate to login page
            logging.info("Navigating to login page...")
            await page.goto(self.login_url, wait_until="networkidle", timeout=30000)
            
            # Wait for SPA to fully load (modern websites need more time)
            logging.info("Waiting for SPA content to load...")
            await asyncio.sleep(3)
            
            # Perform login
            success = await self._perform_login(page)
            
            if success:
                # Save session after successful login
                await self._save_session(page)
                logging.info("Login successful and session saved")
                return True
            else:
                logging.error("Login failed")
                return False
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return False
    
    async def _verify_login_status(self, page: Any) -> bool:
        """Verify if user is currently logged in"""
        try:
            current_url = page.url
            
            # Check if we're on login page
            if 'login' in current_url.lower():
                return False
            
            # Look for user indicators
            user_selectors = [
                '#userNameCss',
                'span:has-text("Vaibhav")',
                '[class*="user"]',
                'h6:contains("Vaibhav")'
            ]
            
            for selector in user_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        user_text = await element.inner_text()
                        if user_text and len(user_text.strip()) > 0:
                            logging.info(f"Found user element: {user_text}")
                            return True
                except:
                    continue
            
            # Check page title
            title = await page.title()
            if title and 'login' not in title.lower():
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Error verifying login status: {e}")
            return False
    
    async def _save_session(self, page: Any) -> None:
        """Save session cookies and storage"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
            
            # Save cookies
            cookies = await page.context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            
            # Save local storage
            local_storage = await page.evaluate("() => Object.assign({}, localStorage)")
            session_storage = await page.evaluate("() => Object.assign({}, sessionStorage)")
            
            session_data = {
                'local_storage': local_storage,
                'session_storage': session_storage,
                'url': page.url,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
                
            logging.info("Session data saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving session: {e}")
    
    async def _restore_session(self, page: Any) -> bool:
        """Restore session from saved cookies and storage"""
        try:
            # Check if session files exist
            if not os.path.exists(self.cookies_file) or not os.path.exists(self.session_file):
                return False
            
            # Load cookies
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Load session data
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is not too old (1 hour)
            current_time = asyncio.get_event_loop().time()
            if current_time - session_data.get('timestamp', 0) > 3600:
                logging.info("Session too old, will re-login")
                return False
            
            # Set cookies
            await page.context.add_cookies(cookies)
            
            # Navigate to last known page
            await page.goto(session_data.get('url', self.login_url), wait_until="domcontentloaded")
            
            # Restore local storage
            if session_data.get('local_storage'):
                for key, value in session_data['local_storage'].items():
                    await page.evaluate(f"localStorage.setItem('{key}', '{value}')")
            
            # Restore session storage
            if session_data.get('session_storage'):
                for key, value in session_data['session_storage'].items():
                    await page.evaluate(f"sessionStorage.setItem('{key}', '{value}')")
            
            await asyncio.sleep(2)
            logging.info("Session restoration attempted")
            return True
            
        except Exception as e:
            logging.error(f"Error restoring session: {e}")
            return False
            await asyncio.sleep(5)
            
            # Click the Login button to show the login form
            await self._click_login_button(page)
            
            # Try to wait for any login-related elements to appear
            await self._wait_for_login_elements(page)
            
            # Look for phone number input field with extended timeout
            logging.info("Looking for phone number input field...")
            phone_input = await self._find_phone_input(page)
            
            # Step 1: Enter phone number
            if not await self._enter_phone_number(page):
                return False
            
            # Step 2: Handle OTP
            if not await self._handle_otp(page):
                return False
            
            # Step 3: Verify login success
            if not await self._verify_login_success(page):
                return False
            
            # Save session for future use
            await self._save_session(page)
            
            logging.info("Login successful!")
            return True
            
        except Exception as e:
            logging.error(f"Login failed with error: {str(e)}")
            return False
    
    async def _wait_for_login_elements(self, page: Any) -> None:
        """Wait for login elements to appear on SPA"""
        try:
            # Wait for any common login elements to appear
            selectors_to_check = [
                "input", "button", "form", 
                "[class*='login']", "[class*='auth']", "[class*='signin']",
                "[id*='login']", "[id*='auth']", "[id*='signin']"
            ]
            
            for selector in selectors_to_check:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    logging.info(f"Found element: {selector}")
                    break
                except PlaywrightTimeoutError:
                    continue
            
            # Additional wait for dynamic content
            await asyncio.sleep(3)
            
        except Exception as e:
            logging.warning(f"Timeout waiting for login elements: {str(e)}")
    
    async def _click_login_button(self, page: Any) -> bool:
        """Click the Login button to show login form"""
        try:
            logging.info("Looking for Login button...")
            
            # Look for login button/link
            login_selectors = [
                'span:has-text("Login")',
                'a:has-text("Login")', 
                'button:has-text("Login")',
                '[role="button"]:has-text("Login")',
                'div:has-text("Login")',
                '*:has-text("Login /")',  # From our analysis: "Login /"
            ]
            
            for selector in login_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        logging.info(f"Found login element: {selector}")
                        await element.click()
                        logging.info("Clicked login button")
                        
                        # Wait for login form to appear
                        await asyncio.sleep(3)
                        return True
                        
                except PlaywrightTimeoutError:
                    continue
            
            logging.warning("Login button not found")
            return False
            
        except Exception as e:
            logging.error(f"Error clicking login button: {str(e)}")
            return False
    
    async def _find_phone_input(self, page: Any) -> Any:
        """Find phone input field with multiple strategies"""
        try:
            # Strategy 1: Try predefined selectors
            for selector in self.selectors["phone_input"].split(", "):
                try:
                    element = await page.wait_for_selector(selector.strip(), timeout=5000)
                    if element:
                        logging.info(f"Found phone input with selector: {selector.strip()}")
                        return element
                except PlaywrightTimeoutError:
                    continue
            
            # Strategy 2: Look for any input that might be a phone field
            logging.info("Trying alternative phone input detection...")
            inputs = await page.query_selector_all("input")
            
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute('type') or 'text'
                input_name = await input_elem.get_attribute('name') or ''
                input_placeholder = await input_elem.get_attribute('placeholder') or ''
                input_id = await input_elem.get_attribute('id') or ''
                
                # Check if this looks like a phone field
                phone_keywords = ['phone', 'mobile', 'number', 'tel', 'contact']
                field_text = f"{input_type} {input_name} {input_placeholder} {input_id}".lower()
                
                if any(keyword in field_text for keyword in phone_keywords) or input_type == 'tel':
                    logging.info(f"Found potential phone input (#{i}): type={input_type}, name={input_name}")
                    return input_elem
            
            # Strategy 3: If still not found, try the first visible input
            logging.info("No phone-specific input found, trying first visible input...")
            for input_elem in inputs:
                if await input_elem.is_visible():
                    logging.info("Using first visible input as phone field")
                    return input_elem
            
            return None
            
        except Exception as e:
            logging.error(f"Error finding phone input: {str(e)}")
            return None

    async def _enter_phone_number(self, page: Any) -> bool:
        """Enter phone number and request OTP"""
        try:
            # Use our improved phone input finder
            phone_input = await self._find_phone_input(page)
            
            if not phone_input:
                logging.error("Phone number input field not found")
                return False
            
            # Clear and enter phone number using Playwright methods
            await phone_input.click()  # Focus the input
            await phone_input.fill('')  # Clear existing content
            await phone_input.type(self.phone_number)  # Type the phone number
            logging.info(f"Entered phone number: {self.phone_number}")
            
            # Wait a bit for any validation
            await asyncio.sleep(1)
            
            # Click send OTP button
            logging.info("Looking for Send OTP button...")
            send_button = None
            
            # Try specific selectors we know work
            otp_button_selectors = [
                "input[type='submit'].custom-button",  # From debug output
                ".custom-button",
                "input[type='submit']",
                "button:has-text('Send OTP')",
                "button:has-text('Send')",
                "button[type='submit']"
            ]
            
            for selector in otp_button_selectors:
                try:
                    send_button = await page.wait_for_selector(selector, timeout=3000)
                    if send_button and await send_button.is_visible() and await send_button.is_enabled():
                        logging.info(f"Found Send OTP button: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not send_button:
                logging.error("Send OTP button not found or not enabled")
                # Debug: show all buttons available
                logging.info("Available buttons:")
                buttons = await page.query_selector_all("button, input[type='submit'], .custom-button")
                for i, btn in enumerate(buttons):
                    try:
                        btn_text = await btn.inner_text()
                        btn_type = await btn.get_attribute('type')
                        btn_class = await btn.get_attribute('class')
                        visible = await btn.is_visible()
                        enabled = await btn.is_enabled()
                        logging.info(f"  Button {i}: text='{btn_text}', type={btn_type}, class={btn_class}, visible={visible}, enabled={enabled}")
                    except:
                        pass
                return False
            
            await send_button.click()
            logging.info("Clicked Send OTP button")
            
            # Wait for OTP input to appear
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logging.error(f"Error entering phone number: {str(e)}")
            return False
    
    async def _handle_otp(self, page: Any) -> bool:
        """Handle OTP input and verification"""
        try:
            # Wait for OTP input field to appear
            logging.info("Waiting for OTP input field...")
            otp_input = None
            
            for selector in self.selectors["otp_input"].split(", "):
                try:
                    otp_input = await page.wait_for_selector(selector.strip(), timeout=10000)
                    if otp_input:
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not otp_input:
                logging.error("OTP input field not found")
                return False
            
            # Get OTP from user
            otp = await self._get_otp()
            if not otp:
                return False
            
            # Enter OTP
            await otp_input.clear()
            await otp_input.fill(otp)
            logging.info("Entered OTP")
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Click verify button
            verify_button = None
            for selector in self.selectors["verify_button"].split(", "):
                try:
                    verify_button = await page.wait_for_selector(selector.strip(), timeout=3000)
                    if verify_button and await verify_button.is_enabled():
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not verify_button:
                logging.error("Verify button not found")
                return False
            
            await verify_button.click()
            logging.info("Clicked verify button")
            
            # Wait for verification
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            logging.error(f"Error handling OTP: {str(e)}")
            return False
    
    async def _get_otp(self) -> Optional[str]:
        """
        Get OTP from user input (for manual entry)
        In production, this could be enhanced to:
        1. Read from SMS API
        2. Read from email
        3. Use automation tools for OTP extraction
        """
        try:
            # For GitHub Actions, check if OTP is provided as environment variable
            github_otp = os.getenv("OTP_CODE")
            if github_otp:
                logging.info("Using OTP from environment variable")
                return github_otp
            
            # For local development, prompt user
            logging.info("Please check your SMS for the OTP code")
            otp = input("Enter the OTP code you received: ").strip()
            
            if len(otp) != 6 or not otp.isdigit():
                logging.error("Invalid OTP format. Please enter 6 digits.")
                return None
            
            return otp
            
        except Exception as e:
            logging.error(f"Error getting OTP: {str(e)}")
            return None
    
    async def _verify_login_success(self, page: Any) -> bool:
        """Verify that login was successful"""
        try:
            # Wait for page to redirect or show success indicators
            await asyncio.sleep(3)
            
            current_url = page.url
            logging.info(f"Current URL after login: {current_url}")
            
            # Check if we're redirected to the main page or dashboard
            if "gopichandacademy.com" in current_url:
                # Additional checks for successful login
                # Look for user-specific elements or absence of login form
                
                # Try to navigate to badminton section to verify access
                try:
                    await page.goto("https://booking.gopichandacademy.com/venuePage/1", timeout=10000)
                    # If we can access this page without being redirected to login, we're logged in
                    if "venuePage" in page.url:
                        return True
                except Exception:
                    pass
            
            # Check for any error messages
            error_elements = await page.query_selector_all(".error, .alert-danger, [class*='error']")
            if error_elements:
                for error_element in error_elements:
                    error_text = await error_element.inner_text()
                    if error_text.strip():
                        logging.error(f"Login error: {error_text}")
                        return False
            
            # If we reach here, assume login was successful
            return True
            
        except Exception as e:
            logging.error(f"Error verifying login success: {str(e)}")
            return False
    
    async def _save_session(self, page: Any):
        """Save session cookies for future use"""
        try:
            # Save cookies
            cookies = await page.context.cookies()
            os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
            
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            
            # Save session storage if needed
            session_data = {
                "url": page.url,
                "timestamp": asyncio.get_event_loop().time(),
                "user_agent": await page.evaluate("navigator.userAgent")
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            logging.info("Session saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving session: {str(e)}")
    
    async def _restore_session(self, page: Any) -> bool:
        """Restore previous session if valid"""
        try:
            if not os.path.exists(self.cookies_file):
                return False
            
            # Load cookies
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # Add cookies to context
            await page.context.add_cookies(cookies)
            
            # Navigate to check if session is still valid
            await page.goto("https://booking.gopichandacademy.com/venuePage/1", timeout=10000)
            
            # If we can access this page, session is valid
            if "venuePage" in page.url:
                return True
            
            return False
            
        except Exception as e:
            logging.debug(f"Could not restore session: {str(e)}")
            return False
    
    def clear_session(self):
        """Clear saved session data"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
            logging.info("Session data cleared")
        except Exception as e:
            logging.error(f"Error clearing session: {str(e)}")
