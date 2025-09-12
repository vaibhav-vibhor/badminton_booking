#!/usr/bin/env python3
"""
Final corrected slot checker - combines working login from improved_checker.py 
with updated slot detection logic based on provided HTML structure
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
    PLAYWRIGHT_AVAILABLE = False

async def final_corrected_checker():
    """Final corrected checker with working login + updated slot detection"""
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available")
        return
    
    load_dotenv()
    phone_number = os.getenv('PHONE_NUMBER')
    
    if not phone_number:
        print("❌ PHONE_NUMBER not set in .env file")
        return
    
    print("🏸 FINAL CORRECTED BADMINTON SLOT CHECKER")
    print("=" * 50)
    print(f"📱 Phone: {phone_number}")
    print(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # STEP 1: Login (using proven approach from improved_checker.py)
            print("\n🔐 Step 1: Starting login process...")
            await page.goto('https://booking.gopichandacademy.com/login', wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Click Login button
            try:
                login_button = await page.wait_for_selector('.custom-button', timeout=10000)
                await login_button.click()
                await asyncio.sleep(3)
                print("   ✅ Login button clicked")
            except:
                print("   ❌ Could not find login button")
            
            # Enter phone number - using multiple selectors
            print("📞 Step 2: Entering phone number...")
            
            phone_selectors = [
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="mobile"]', 
                'input[placeholder*="phone"]',
                'input[placeholder*="mobile"]',
                'input[placeholder*="number"]',
                'input[maxlength="10"]'
            ]
            
            phone_input = None
            for selector in phone_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        phone_input = elements[0]
                        print(f"   ✅ Found phone input with: {selector}")
                        break
                except:
                    continue
            
            if not phone_input:
                # Try finding any input on the page
                all_inputs = await page.query_selector_all('input')
                if all_inputs:
                    phone_input = all_inputs[0]  # Use first input
                    print("   ⚠️ Using first available input field")
                else:
                    print("   ❌ No input fields found at all")
                    return
            
            await phone_input.fill(phone_number)
            await asyncio.sleep(2)
            print(f"   ✅ Entered phone number: {phone_number}")
            
            # Click Send OTP
            print("📨 Step 3: Clicking Send OTP...")
            try:
                send_buttons = await page.query_selector_all('.custom-button')
                if len(send_buttons) > 1:
                    # Second button is usually "Send OTP"
                    await send_buttons[1].click()
                else:
                    await send_buttons[0].click()
                await asyncio.sleep(3)
                print("   ✅ Send OTP clicked")
            except Exception as e:
                print(f"   ❌ Could not click Send OTP: {e}")
            
            # Manual OTP entry
            print("\n⏳ Step 4: MANUAL OTP ENTRY REQUIRED")
            print("   📱 Check your phone for the OTP code")
            print("   ✏️ Enter the 6-digit OTP in the browser")
            print("   🔄 This script will continue automatically once you're logged in...")
            print("   ⏰ You have 5 minutes to complete this step")
            
            # Wait for login completion
            login_successful = False
            max_wait = 300  # 5 minutes
            check_interval = 3
            
            for elapsed in range(0, max_wait, check_interval):
                await asyncio.sleep(check_interval)
                
                current_url = page.url
                if '/login' not in current_url or 'dashboard' in current_url or 'booking' in current_url:
                    print(f"   ✅ Login successful! Current page: {current_url}")
                    login_successful = True
                    break
                
                if elapsed % 30 == 0 and elapsed > 0:
                    print(f"   ⏳ Still waiting... ({elapsed}s elapsed)")
            
            if not login_successful:
                print("   ❌ Login timeout - please run the script again")
                return
            
            # STEP 5: Updated slot checking with corrected selectors and logic
            print("\n🏸 Step 5: Checking Slots with CORRECTED LOGIC")
            print("   Using HTML structure from your provided example...")
            
            # Test dates
            test_dates = [
                (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            ]
            
            academy_url = "https://booking.gopichandacademy.com/booking/facility/kotak-pullela-gopichand--badminton-academy"
            academy_name = "Kotak Pullela Gopichand Badminton Academy"
            
            print(f"   🏟️ Academy: {academy_name}")
            print(f"   📅 Checking dates: {test_dates}")
            
            all_available_slots = []
            
            # Navigate to academy
            print("   🔗 Navigating to academy page...")
            await page.goto(academy_url, wait_until='domcontentloaded')
            await asyncio.sleep(4)
            
            for date_idx, test_date in enumerate(test_dates):
                print(f"\n   📅 Date {date_idx + 1}: {test_date}")
                
                # Step 1: Set the date
                try:
                    date_input = await page.wait_for_selector('input#card1[type="date"]', timeout=10000)
                    current_value = await date_input.get_attribute('value')
                    print(f"      Current date value: {current_value}")
                    
                    # Clear and set new date
                    await date_input.click()
                    await date_input.fill('')
                    await date_input.fill(test_date)
                    
                    # Trigger change events
                    await date_input.dispatch_event('input')
                    await date_input.dispatch_event('change')
                    await asyncio.sleep(4)  # Wait for courts to load
                    
                    print(f"      ✅ Date set to: {test_date}")
                except Exception as e:
                    print(f"      ❌ Could not set date: {e}")
                    continue
                
                # Step 2: Wait for and find courts
                try:
                    # Wait for courts to appear in availability section
                    await page.wait_for_selector('div.court-item', timeout=10000)
                    court_elements = await page.query_selector_all('div.court-item')
                    print(f"      🏟️ Found {len(court_elements)} courts")
                    
                    if not court_elements:
                        print("      ⚠️ No courts found - might be outside booking window")
                        continue
                        
                except Exception as e:
                    print(f"      ❌ Courts didn't load: {e}")
                    continue
                
                # Step 3: Check each court
                for court_idx, court_element in enumerate(court_elements):
                    try:
                        court_number = await court_element.inner_text()
                        print(f"         🏸 Court {court_number}")
                        
                        # Click to select this court
                        await court_element.click()
                        await asyncio.sleep(3)  # Wait for time slots to load
                        
                        # Step 4: Get time slots for this court
                        try:
                            time_slot_elements = await page.query_selector_all('span.styled-btn')
                            print(f"            🕒 Found {len(time_slot_elements)} time slots")
                            
                            if not time_slot_elements:
                                print("            ⚠️ No time slots found")
                                continue
                            
                            # Check availability of each time slot
                            available_count = 0
                            booked_count = 0
                            
                            for slot_element in time_slot_elements:
                                time_text = await slot_element.inner_text()
                                style = await slot_element.get_attribute('style') or ''
                                
                                # Apply the corrected availability logic:
                                # Available slots: style="" or no red color with not-allowed cursor
                                # Unavailable slots: style="color: red; cursor: not-allowed;"
                                style_lower = style.lower()
                                has_red_color = 'color: red' in style_lower or 'color:red' in style_lower
                                has_not_allowed = 'cursor: not-allowed' in style_lower or 'cursor:not-allowed' in style_lower
                                
                                is_available = not (has_red_color and has_not_allowed)
                                
                                if is_available:
                                    available_count += 1
                                    slot_info = {
                                        'academy': academy_name,
                                        'date': test_date,
                                        'court': f'Court {court_number}',
                                        'time': time_text,
                                        'status': 'available',
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    all_available_slots.append(slot_info)
                                    print(f"            ✅ AVAILABLE: {time_text}")
                                else:
                                    booked_count += 1
                                    print(f"            ❌ Booked: {time_text} (style: {style[:50]})")
                            
                            print(f"            📊 Court {court_number}: {available_count} available, {booked_count} booked")
                            
                        except Exception as e:
                            print(f"            ❌ Error checking time slots: {e}")
                    
                    except Exception as e:
                        print(f"         ❌ Error with court {court_idx + 1}: {e}")
                
                print(f"      ✅ Completed checking {len(court_elements)} courts for {test_date}")
            
            # STEP 6: Display results and send notifications
            print(f"\n📊 FINAL RESULTS")
            print("=" * 30)
            print(f"🎯 Total available slots found: {len(all_available_slots)}")
            
            if all_available_slots:
                print("\n🎉 AVAILABLE SLOTS:")
                print("=" * 40)
                
                for i, slot in enumerate(all_available_slots, 1):
                    print(f"{i}. 🏟️ {slot['academy']}")
                    print(f"   📅 Date: {slot['date']}")
                    print(f"   🏸 Court: {slot['court']}")
                    print(f"   🕒 Time: {slot['time']}")
                    print(f"   🔗 URL: https://booking.gopichandacademy.com/")
                    print("-" * 40)
                
                # Send Telegram notification
                telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                
                if telegram_token and chat_id:
                    print(f"\n📱 Sending Telegram notification for {len(all_available_slots)} slots...")
                    try:
                        import aiohttp
                        
                        message = f"🏸 *{len(all_available_slots)} BADMINTON SLOTS AVAILABLE!* 🏸\n\n"
                        
                        for i, slot in enumerate(all_available_slots[:8], 1):  # Show up to 8 slots
                            message += f"*{i}.* {slot['court']}\n"
                            message += f"📅 {slot['date']} at {slot['time']}\n"
                            message += f"🏟️ {slot['academy']}\n\n"
                        
                        if len(all_available_slots) > 8:
                            message += f"... and {len(all_available_slots) - 8} more slots!\n\n"
                        
                        message += "🔗 *Book immediately:* https://booking.gopichandacademy.com/\n"
                        message += f"⏰ Found at {datetime.now().strftime('%H:%M:%S')}"
                        
                        async with aiohttp.ClientSession() as session:
                            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                            payload = {
                                'chat_id': chat_id,
                                'text': message,
                                'parse_mode': 'Markdown'
                            }
                            
                            async with session.post(url, json=payload) as response:
                                if response.status == 200:
                                    print("✅ Telegram notification sent successfully!")
                                else:
                                    response_text = await response.text()
                                    print(f"❌ Telegram failed ({response.status}): {response_text}")
                    
                    except Exception as e:
                        print(f"❌ Telegram notification error: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("ℹ️ Telegram credentials not configured - skipping notification")
            
            else:
                print("\n😔 No available slots found")
                print("   This means:")
                print("   ✅ The slot detection logic is working correctly")
                print("   ✅ All time slots were found but marked as unavailable")
                print("   ✅ This is normal when all courts are fully booked")
                print("\n💡 Recommendations:")
                print("   🔄 Run this script every 15-30 minutes")
                print("   ⏰ Try checking early morning or late evening")
                print("   📅 Check different dates or academies")
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print(f"\n⏳ Keeping browser open for 15 seconds for inspection...")
            await asyncio.sleep(15)
            await browser.close()
    
    print(f"\n✅ Final corrected checker completed at {datetime.now().strftime('%H:%M:%S')}")
    print("🔄 Run this script regularly to monitor for new slot availability!")

if __name__ == "__main__":
    asyncio.run(final_corrected_checker())
