#!/usr/bin/env python3
"""
Fixed Badminton Checker with Proper Session Management
This version ensures the session persists across page navigations
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from playwright.async_api import async_playwright
from config_handler import ConfigHandler
from notification_handler import NotificationHandler

def get_next_booking_dates(days_ahead=7):
    """Get the next available booking dates"""
    today = datetime.now()
    dates = []
    
    for i in range(1, days_ahead + 1):  # Start from tomorrow
        next_date = today + timedelta(days=i)
        dates.append(next_date.strftime('%Y-%m-%d'))
    
    return dates

async def check_login_status(page):
    """Check if we're still logged in"""
    current_url = page.url
    print(f"   Checking login status - Current URL: {current_url}")
    
    # Check for login page indicators
    if 'login' in current_url.lower():
        print("   ❌ On login page")
        return False
    
    # Check for user elements that indicate logged in state
    try:
        user_indicators = [
            'span:has-text("Vaibhav")',
            '#userNameCss',
            'span[id="userNameCss"]',
            '.user',
            '[class*="user"]',
            'h6:has-text("Vaibhav")'
        ]
        
        for selector in user_indicators:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    print(f"   ✅ Found user element: {selector} = '{text}'")
                    return True
                else:
                    print(f"   ❌ Not found: {selector}")
            except Exception as e:
                print(f"   ⚠️ Error checking {selector}: {e}")
    except Exception as e:
        print(f"   ❌ Error in login check: {e}")
    
    # Try to find any indication we're logged in
    try:
        # Look for logout button or user menu
        logout_indicators = ['logout', 'Logout', 'Log out']
        for text in logout_indicators:
            element = await page.query_selector(f'*:has-text("{text}")')
            if element:
                print(f"   ✅ Found logout indicator: {text}")
                return True
    except:
        pass
    
    # Check page title or content
    try:
        title = await page.title()
        print(f"   Page title: {title}")
        if 'login' not in title.lower() and title.strip():
            print("   ✅ Page title suggests logged in")
            return True
    except:
        pass
    
    print("   ❌ No login indicators found")
    return False

async def ensure_logged_in(page, config):
    """Ensure we're logged in, re-login if necessary"""
    
    if await check_login_status(page):
        print("✅ Already logged in")
        return True
    
    print("🔐 Need to login/re-login...")
    
    # Go to login page
    await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
    await asyncio.sleep(3)
    
    # Click Login button
    try:
        login_btn = await page.wait_for_selector('span:has-text("Login")', timeout=10000)
        await login_btn.click()
        await asyncio.sleep(3)
    except:
        print("❌ Could not find login button")
        return False
    
    # Enter phone number
    try:
        phone_input = await page.wait_for_selector('input', timeout=10000)
        await phone_input.click()
        await phone_input.fill('')
        await phone_input.type(config.phone_number)
        print(f"📱 Entered phone: {config.phone_number}")
    except:
        print("❌ Could not find phone input")
        return False
    
    # Click Send OTP
    try:
        send_button_selectors = [
            "input[type='submit'].custom-button",
            ".custom-button",
            "input[type='submit']"
        ]
        
        for selector in send_button_selectors:
            try:
                send_button = await page.wait_for_selector(selector, timeout=3000)
                if send_button and await send_button.is_visible():
                    await send_button.click()
                    print("📤 Send OTP clicked")
                    break
            except:
                continue
    except:
        print("❌ Could not click Send OTP")
        return False
    
    # Wait for manual OTP entry
    print("\n" + "="*50)
    print("📱 MANUAL OTP ENTRY REQUIRED")
    print("="*50)
    print("Please:")
    print("1. Check your phone for OTP")
    print("2. Enter OTP in the browser")
    print("3. Click Submit/Verify")
    print("4. Wait for successful login")
    print("\nPress ENTER when login is complete...")
    print("="*50)
    
    input("Press ENTER after login: ")
    
    # Verify login
    await asyncio.sleep(2)
    if await check_login_status(page):
        print("✅ Login successful!")
        return True
    else:
        print("❌ Login failed or incomplete")
        return False

async def check_academy_slots_with_session(page, academy_info, test_dates, config):
    """Check slots for an academy while maintaining session"""
    
    academy_url = academy_info['url']
    academy_name = academy_info['name']
    
    print(f"\n🏟️ Checking: {academy_name}")
    print(f"   URL: {academy_url}")
    
    all_slots = []
    
    try:
        # Navigate to academy page
        print("   🔗 Navigating to academy page...")
        await page.goto(academy_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Check if we got redirected to login
        if 'login' in page.url.lower():
            print("   ⚠️ Redirected to login - session lost")
            if not await ensure_logged_in(page, config):
                return []
            
            # Try navigating again
            await page.goto(academy_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        # Verify we're on the right page
        current_url = page.url
        if 'login' in current_url.lower():
            print("   ❌ Still on login page - cannot proceed")
            return []
        
        print(f"   ✅ Successfully on: {current_url}")
        
        # Look for the booking form
        try:
            # Try multiple selectors for the form
            form_selectors = [
                'form.contact-form',
                'form',
                '.contact-form',
                '.booking-form',
                '.checkout-widget'
            ]
            
            form = None
            for selector in form_selectors:
                try:
                    form = await page.wait_for_selector(selector, timeout=3000)
                    if form:
                        print(f"   ✅ Found booking form: {selector}")
                        break
                except:
                    continue
            
            if not form:
                print("   ⚠️ No standard form found, looking for date input directly...")
                # Try to find date input directly
                date_input = await page.query_selector('input#card1[type="date"]')
                if date_input:
                    print("   ✅ Found date input - can proceed")
                else:
                    print("   ❌ No date input found")
                    
                    # Debug: Let's see what's actually on the page
                    print("   🔍 Page debugging:")
                    inputs = await page.query_selector_all('input')
                    print(f"      Found {len(inputs)} input elements total")
                    
                    forms = await page.query_selector_all('form')
                    print(f"      Found {len(forms)} form elements total")
                    
                    # Check page content
                    page_text = await page.inner_text('body')
                    if 'Date' in page_text:
                        print("      ✅ Page contains 'Date' text")
                    if 'Court' in page_text:
                        print("      ✅ Page contains 'Court' text")
                    if 'Availability' in page_text:
                        print("      ✅ Page contains 'Availability' text")
                        
                    return []
        except Exception as e:
            print(f"   ❌ Error finding booking form: {e}")
            return []
        
        # Check each date
        for date in test_dates:
            print(f"\n   📅 Checking date: {date}")
            
            try:
                # Set the date
                date_input = await page.wait_for_selector('input#card1[type="date"]', timeout=10000)
                await date_input.click()
                await date_input.fill('')
                await date_input.fill(date)
                await date_input.dispatch_event('change')
                
                print("      ✅ Date set")
                await asyncio.sleep(4)  # Wait for courts to load
                
                # Look for courts
                try:
                    await page.wait_for_selector('div.court-item', timeout=15000)
                    courts = await page.query_selector_all('div.court-item')
                    print(f"      🏸 Found {len(courts)} courts")
                    
                    if not courts:
                        print("      ⚠️ No courts available for this date")
                        continue
                        
                except:
                    print("      ❌ No courts appeared - may be outside booking window")
                    continue
                
                # Check each court
                for i, court in enumerate(courts):
                    try:
                        court_number = await court.inner_text()
                        print(f"         Court {court_number}:")
                        
                        # Click court
                        await court.click()
                        await asyncio.sleep(3)
                        
                        # Get time slots
                        try:
                            time_slots = await page.query_selector_all('span.styled-btn')
                            print(f"            Found {len(time_slots)} time slots")
                            
                            available_count = 0
                            for slot in time_slots:
                                time_text = await slot.inner_text()
                                style = await slot.get_attribute('style') or ''
                                
                                # Check availability using corrected logic
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
                                        'status': 'available',
                                        'url': academy_url
                                    }
                                    all_slots.append(slot_info)
                                    print(f"            ✅ AVAILABLE: {time_text}")
                                else:
                                    print(f"            ❌ Booked: {time_text}")
                            
                            print(f"            📊 {available_count} available slots")
                            
                        except Exception as e:
                            print(f"            ❌ Error getting time slots: {e}")
                    
                    except Exception as e:
                        print(f"         ❌ Error with court {i+1}: {e}")
                
                print(f"      ✅ Date {date} complete")
                
            except Exception as e:
                print(f"      ❌ Error setting date {date}: {e}")
        
        print(f"   ✅ Academy check complete: {len(all_slots)} slots found")
        
    except Exception as e:
        print(f"   ❌ Academy check failed: {e}")
    
    return all_slots

async def fixed_slot_checker():
    """Fixed slot checker with proper session management"""
    
    print("🏸 FIXED Badminton Slot Checker - Session Management")
    print("=" * 60)
    print(f"⏰ Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load configuration
        config = ConfigHandler()
        notification = NotificationHandler(
            config.telegram_bot_token,
            config.telegram_chat_id
        )
        
        # Get dates to check
        dates_to_check = get_next_booking_dates(5)  # Check next 5 days
        print(f"📅 Dates to check: {', '.join(dates_to_check)}")
        
        async with async_playwright() as p:
            # Launch browser with session persistence
            browser = await p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # Create context with session persistence
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Initial login
            print("\n🔐 INITIAL LOGIN")
            print("-" * 30)
            
            if not await ensure_logged_in(page, config):
                print("❌ Initial login failed")
                return
            
            # Test academies (start with just Kotak)
            academies_to_test = {
                'kotak': {
                    'name': 'Kotak Pullela Gopichand Badminton Academy',
                    'url': 'https://booking.gopichandacademy.com/venue-details/1'
                }
            }
            
            print(f"\n🏟️ CHECKING {len(academies_to_test)} ACADEMIES")
            print("-" * 40)
            
            all_available_slots = []
            
            # Check each academy
            for academy_key, academy_info in academies_to_test.items():
                slots = await check_academy_slots_with_session(
                    page, academy_info, dates_to_check, config
                )
                all_available_slots.extend(slots)
            
            # Results
            print(f"\n📊 FINAL RESULTS")
            print("=" * 30)
            print(f"🎯 Total available slots: {len(all_available_slots)}")
            
            if all_available_slots:
                print("\n🎉 AVAILABLE SLOTS FOUND!")
                print("-" * 40)
                
                for i, slot in enumerate(all_available_slots, 1):
                    print(f"{i}. 🏟️ {slot['academy']}")
                    print(f"   📅 {slot['date']} at {slot['time']}")
                    print(f"   🏸 {slot['court']}")
                    print(f"   🔗 {slot['url']}")
                    print()
                
                # Send notification
                try:
                    await notification.send_slot_notifications(all_available_slots)
                    print("📱 Telegram notification sent!")
                except Exception as e:
                    print(f"❌ Notification failed: {e}")
                    
            else:
                print("😔 No available slots found")
                print("   This usually means all courts are booked")
                print("   ✅ The system is working correctly")
            
            print(f"\n⏳ Keeping browser open for 15 seconds...")
            await asyncio.sleep(15)
            await browser.close()
            
        print(f"✅ Check completed at: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fixed_slot_checker())
