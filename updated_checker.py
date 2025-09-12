#!/usr/bin/env python3
"""
Updated improved checker with corrected slot detection logic
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install playwright: pip install playwright")
    PLAYWRIGHT_AVAILABLE = False

async def updated_slot_checker():
    """Updated slot checker with correct HTML selectors and logic"""
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available - please run: pip install playwright")
        return
    
    # Load environment
    load_dotenv()
    
    phone_number = os.getenv('PHONE_NUMBER')
    if not phone_number:
        print("❌ PHONE_NUMBER not set in .env file")
        return
    
    print("🏸 UPDATED BADMINTON SLOT CHECKER")
    print("=" * 50)
    print(f"📱 Phone: {phone_number}")
    print(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to login
            print("\\n🔗 Step 1: Navigating to login page...")
            await page.goto('https://booking.gopichandacademy.com/login', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Step 2: Click Login button (required for SPA websites)
            print("🔐 Step 2: Clicking Login button...")
            try:
                login_button = await page.wait_for_selector('.custom-button', timeout=5000)
                await login_button.click()
                await asyncio.sleep(2)
                print("   ✅ Login button clicked")
            except:
                print("   ⚠️ Login button not found, continuing...")
            
            # Step 3: Enter phone number
            print("📞 Step 3: Entering phone number...")
            
            phone_selectors = [
                'input[type="tel"]',
                'input[name*="phone"]', 
                'input[placeholder*="phone"]',
                'input[placeholder*="mobile"]',
                'input[placeholder*="number"]'
            ]
            
            phone_input = None
            for selector in phone_selectors:
                try:
                    phone_input = await page.wait_for_selector(selector, timeout=3000)
                    if phone_input:
                        print(f"   ✅ Found phone input: {selector}")
                        break
                except:
                    continue
            
            if not phone_input:
                print("   ❌ Could not find phone input field")
                return
                
            await phone_input.fill(phone_number)
            await asyncio.sleep(1)
            
            # Step 4: Click Send OTP
            print("📨 Step 4: Clicking Send OTP...")
            try:
                send_otp_button = await page.wait_for_selector('.custom-button', timeout=5000)
                await send_otp_button.click()
                await asyncio.sleep(2)
                print("   ✅ Send OTP clicked")
            except Exception as e:
                print(f"   ❌ Could not click Send OTP: {e}")
                return
            
            # Step 5: Manual OTP entry
            print("\\n⏳ Step 5: MANUAL OTP ENTRY")
            print("   📱 Check your phone for OTP")
            print("   ✏️ Enter OTP in the browser")
            print("   🔄 The script will automatically continue once you're logged in")
            
            # Wait for login to complete by checking for redirect
            max_wait_time = 300  # 5 minutes
            wait_interval = 2
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                current_url = page.url
                
                # Check if we're logged in (no longer on login page)
                if '/login' not in current_url and 'booking.gopichandacademy.com' in current_url:
                    print("   ✅ Login successful! Redirected to:", current_url)
                    break
                
                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval
                
                # Progress indicator
                if elapsed_time % 20 == 0:
                    print(f"   ⏳ Waiting... ({elapsed_time}s elapsed)")
            
            if elapsed_time >= max_wait_time:
                print("   ❌ Login timeout - please try again")
                return
            
            # Step 6: Updated slot checking with correct selectors
            print("\\n🏸 Step 6: Checking Available Slots with Updated Logic")
            
            # Test dates
            test_dates = [
                (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            ]
            
            # Academy to test
            kotak_url = "https://booking.gopichandacademy.com/booking/facility/kotak-pullela-gopichand--badminton-academy"
            academy_name = "Kotak Pullela Gopichand Badminton Academy"
            
            print(f"   🏟️ Testing: {academy_name}")
            print(f"   📅 Dates: {test_dates}")
            
            all_available_slots = []
            
            # Navigate to academy
            await page.goto(kotak_url, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Check each date
            for date in test_dates:
                print(f"\\n   📅 Checking date: {date}")
                
                # Set date
                try:
                    date_input = await page.wait_for_selector('input#card1[type="date"]', timeout=10000)
                    await date_input.fill(date)
                    await date_input.dispatch_event('change')
                    await asyncio.sleep(3)
                    print("      ✅ Date set successfully")
                except Exception as e:
                    print(f"      ❌ Could not set date: {e}")
                    continue
                
                # Wait for courts to appear
                try:
                    await page.wait_for_selector('div.court-item', timeout=10000)
                    court_elements = await page.query_selector_all('div.court-item')
                    print(f"      🏟️ Found {len(court_elements)} courts")
                except Exception as e:
                    print(f"      ❌ No courts found: {e}")
                    continue
                
                # Check each court
                for i, court_element in enumerate(court_elements):
                    try:
                        court_number = await court_element.inner_text()
                        print(f"         🏸 Checking Court {court_number}")
                        
                        # Click court
                        await court_element.click()
                        await asyncio.sleep(2)
                        
                        # Wait for time slots
                        try:
                            await page.wait_for_selector('span.styled-btn', timeout=5000)
                            time_slots = await page.query_selector_all('span.styled-btn')
                            print(f"            🕒 Found {len(time_slots)} time slots")
                            
                            # Check each time slot
                            for slot in time_slots:
                                time_text = await slot.inner_text()
                                style = await slot.get_attribute('style') or ''
                                
                                # Determine availability using updated logic
                                is_red = 'color: red' in style.lower()
                                is_not_allowed = 'cursor: not-allowed' in style.lower()
                                is_available = not (is_red and is_not_allowed)
                                
                                if is_available:
                                    slot_info = {
                                        'academy': academy_name,
                                        'date': date,
                                        'court': f'Court {court_number}',
                                        'time': time_text,
                                        'status': 'available'
                                    }
                                    all_available_slots.append(slot_info)
                                    print(f"            ✅ AVAILABLE: {time_text}")
                                else:
                                    print(f"            ❌ Booked: {time_text}")
                        
                        except Exception as e:
                            print(f"            ❌ No time slots: {e}")
                    
                    except Exception as e:
                        print(f"         ❌ Error with court {i+1}: {e}")
            
            # Display final results
            print(f"\\n📊 FINAL RESULTS: {len(all_available_slots)} Available Slots Found")
            
            if all_available_slots:
                print("\\n🎉 AVAILABLE SLOTS:")
                for slot in all_available_slots:
                    print(f"   🏟️ {slot['academy']}")
                    print(f"      📅 Date: {slot['date']}")
                    print(f"      🏸 Court: {slot['court']}")
                    print(f"      🕒 Time: {slot['time']}")
                    print("      " + "="*40)
                
                # Send Telegram notification if configured
                telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                
                if telegram_token and chat_id:
                    print(f"\\n📱 Sending Telegram notification...")
                    try:
                        import aiohttp
                        
                        message = f"🏸 *{len(all_available_slots)} Badminton Slots Available!*\\n\\n"
                        
                        for i, slot in enumerate(all_available_slots[:5], 1):  # Show first 5
                            message += f"*{i}.* {slot['court']}\\n"
                            message += f"📅 {slot['date']} at {slot['time']}\\n"
                            message += f"🏟️ {slot['academy']}\\n\\n"
                        
                        if len(all_available_slots) > 5:
                            message += f"... and {len(all_available_slots) - 5} more slots!\\n\\n"
                        
                        message += "🔗 Book now: https://booking.gopichandacademy.com/"
                        
                        async with aiohttp.ClientSession() as session:
                            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                            payload = {
                                'chat_id': chat_id,
                                'text': message,
                                'parse_mode': 'Markdown'
                            }
                            
                            async with session.post(url, json=payload) as response:
                                if response.status == 200:
                                    print("✅ Telegram notification sent!")
                                else:
                                    print(f"❌ Telegram failed: {response.status}")
                    except Exception as e:
                        print(f"❌ Telegram error: {e}")
                else:
                    print("ℹ️ Telegram not configured")
            
            else:
                print("\\nℹ️ No available slots found")
                print("   This usually means all slots are currently booked")
                print("   Run the script regularly to catch newly available slots!")
            
        except Exception as e:
            print(f"\\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\\n⏳ Closing browser in 10 seconds...")
            await asyncio.sleep(10)
            await browser.close()
    
    print(f"\\n✅ Updated checker completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(updated_slot_checker())
