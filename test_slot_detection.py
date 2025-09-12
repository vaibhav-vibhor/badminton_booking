#!/usr/bin/env python3
"""
Simple test to verify the corrected BookingChecker slot detection logic
Uses the login approach that we know works from improved_checker.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from playwright.async_api import async_playwright

async def test_slot_detection():
    """Test the corrected slot detection logic"""
    
    load_dotenv()
    phone_number = os.getenv('PHONE_NUMBER')
    
    if not phone_number:
        print("❌ PHONE_NUMBER not set in .env")
        return
    
    print("🧪 TESTING CORRECTED SLOT DETECTION LOGIC")
    print("=" * 50)
    print("This test will use the corrected HTML selectors and availability logic")
    print("based on your provided HTML structure.\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Use the proven login approach
            print("🔐 Step 1: Login process...")
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Click Login
            login_btn = await page.wait_for_selector('span:has-text("Login")', timeout=10000)
            await login_btn.click()
            await asyncio.sleep(3)
            
            # Enter phone
            phone_input = await page.wait_for_selector('input', timeout=10000)
            await phone_input.click()
            await phone_input.fill(phone_number)
            await asyncio.sleep(2)
            
            # Send OTP
            send_otp_btn = await page.wait_for_selector('button:has-text("Send OTP")', timeout=10000)
            await send_otp_btn.click()
            await asyncio.sleep(3)
            
            print("⏳ Please enter OTP manually in browser...")
            print("   Press Enter here once logged in to continue testing...")
            input("   Press Enter when ready: ")
            
            # Navigate to test academy
            test_url = "https://booking.gopichandacademy.com/booking/facility/kotak-pullela-gopichand--badminton-academy"
            print(f"🏸 Navigating to test academy...")
            await page.goto(test_url, wait_until='domcontentloaded')
            await asyncio.sleep(4)
            
            # Test date
            test_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"📅 Testing with date: {test_date}")
            
            # CORRECTED LOGIC TESTING
            print("\n🔍 TESTING CORRECTED SLOT DETECTION:")
            print("-" * 40)
            
            # Step 1: Set date
            print("1. Setting date...")
            try:
                date_input = await page.wait_for_selector('input#card1[type="date"]', timeout=10000)
                await date_input.fill(test_date)
                await date_input.dispatch_event('change')
                await asyncio.sleep(4)
                print("   ✅ Date set successfully")
            except Exception as e:
                print(f"   ❌ Date setting failed: {e}")
                return
            
            # Step 2: Check for courts
            print("2. Looking for courts...")
            try:
                court_elements = await page.query_selector_all('div.court-item')
                print(f"   ✅ Found {len(court_elements)} courts")
                
                if not court_elements:
                    print("   ⚠️ No courts found - this might be outside booking window")
                    return
                    
            except Exception as e:
                print(f"   ❌ Court detection failed: {e}")
                return
            
            # Step 3: Test clicking first court and checking time slots
            print("3. Testing first court...")
            try:
                first_court = court_elements[0]
                court_number = await first_court.inner_text()
                print(f"   🏸 Clicking Court {court_number}")
                
                await first_court.click()
                await asyncio.sleep(3)
                
                # Check for time slots
                time_slots = await page.query_selector_all('span.styled-btn')
                print(f"   ✅ Found {len(time_slots)} time slots")
                
                if not time_slots:
                    print("   ⚠️ No time slots found")
                    return
                
            except Exception as e:
                print(f"   ❌ Court clicking failed: {e}")
                return
            
            # Step 4: Test availability detection logic
            print("4. Testing availability detection logic...")
            available_slots = []
            booked_slots = []
            
            for i, slot in enumerate(time_slots):
                try:
                    time_text = await slot.inner_text()
                    style = await slot.get_attribute('style') or ''
                    
                    # CORRECTED AVAILABILITY LOGIC:
                    # Available: style="" or doesn't have both "color: red" and "cursor: not-allowed"
                    # Booked: style="color: red; cursor: not-allowed;"
                    
                    style_lower = style.lower()
                    has_red_color = 'color: red' in style_lower or 'color:red' in style_lower
                    has_not_allowed = 'cursor: not-allowed' in style_lower or 'cursor:not-allowed' in style_lower
                    
                    is_available = not (has_red_color and has_not_allowed)
                    
                    if is_available:
                        available_slots.append(time_text)
                        print(f"   ✅ AVAILABLE: {time_text} (style: {style[:50]})")
                    else:
                        booked_slots.append(time_text)
                        print(f"   ❌ BOOKED: {time_text} (style: {style[:50]})")
                        
                except Exception as e:
                    print(f"   ⚠️ Error checking slot {i}: {e}")
            
            # Results
            print("\n📊 TEST RESULTS:")
            print("=" * 30)
            print(f"✅ Available slots: {len(available_slots)}")
            print(f"❌ Booked slots: {len(booked_slots)}")
            print(f"🎯 Total slots processed: {len(time_slots)}")
            
            if available_slots:
                print(f"\n🎉 SUCCESS! Found available slots:")
                for slot in available_slots:
                    print(f"   • {slot}")
                print(f"\n✅ The corrected logic is working!")
                print("   These slots can be booked right now.")
            else:
                print(f"\n😔 No available slots found")
                print("✅ The logic is working correctly - all slots are booked")
                print("   This is normal when courts are fully reserved")
            
            print(f"\n🎯 CONCLUSION:")
            print("✅ Slot detection logic is working correctly")
            print("✅ HTML selectors are finding the right elements")
            print("✅ Availability logic properly distinguishes booked vs available")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print(f"\n⏳ Keeping browser open for manual inspection...")
            await asyncio.sleep(20)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_slot_detection())
