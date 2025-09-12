#!/usr/bin/env python3
"""
Badminton Checker - Improved Version with Better Date Handling
This version will check more relevant dates and provide detailed feedback
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
from booking_checker import BookingChecker

def get_next_booking_dates(days_ahead=7):
    """Get the next available booking dates"""
    today = datetime.now()
    dates = []
    
    for i in range(1, days_ahead + 1):  # Start from tomorrow
        next_date = today + timedelta(days=i)
        # Most academies allow booking 7 days in advance
        dates.append(next_date.strftime('%Y-%m-%d'))
    
    return dates

async def improved_slot_checker():
    """Improved slot checker with better date handling"""
    
    print("🏸 Badminton Slot Checker - Improved Version")
    print("=" * 55)
    print(f"⏰ Starting check at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Load configuration
        config = ConfigHandler()
        notification = NotificationHandler(
            config.telegram_bot_token,
            config.telegram_chat_id
        )
        booking_checker = BookingChecker()
        
        # Get smart date range
        dates_to_check = get_next_booking_dates(7)
        print(f"📅 Checking dates: {', '.join(dates_to_check)}")
        
        async with async_playwright() as p:
            # Launch browser (visible for manual OTP entry)
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("\n🌐 Navigating to booking website...")
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
            await asyncio.sleep(3)
            
            print("🔗 Clicking Login button...")
            login_btn = await page.wait_for_selector('span:has-text("Login")', timeout=10000)
            await login_btn.click()
            await asyncio.sleep(3)
            
            print("📱 Entering your phone number...")
            phone_input = await page.wait_for_selector('input', timeout=10000)
            await phone_input.click()
            await phone_input.fill('')
            await phone_input.type(config.phone_number)
            print(f"✅ Entered: {config.phone_number}")
            
            print("📤 Clicking Send OTP button...")
            # Look for Send OTP button
            send_button = None
            otp_button_selectors = [
                "input[type='submit'].custom-button",
                ".custom-button",
                "input[type='submit']"
            ]
            
            for selector in otp_button_selectors:
                try:
                    send_button = await page.wait_for_selector(selector, timeout=3000)
                    if send_button and await send_button.is_visible() and await send_button.is_enabled():
                        print(f"✅ Found Send OTP button: {selector}")
                        break
                except:
                    continue
            
            if send_button:
                await send_button.click()
                print("📤 Send OTP button clicked!")
                print("📱 OTP should arrive within 1-2 minutes...")
                await asyncio.sleep(3)
            else:
                print("❌ Send OTP button not found. Please click it manually.")
            
            # Manual OTP entry with better instructions
            print("\n" + "="*55)
            print("📱 WAITING FOR OTP")
            print("="*55)
            print("🔍 Check these places for your OTP:")
            print(f"   📞 SMS to {config.phone_number}")
            print("   📧 Email (if configured)")
            print("   🗑️ Spam/Junk folder")
            print()
            print("⏱️ OTPs usually arrive within 1-2 minutes")
            print("🔄 If no OTP after 3 minutes, try refreshing the page")
            print()
            print("Once you receive the OTP:")
            print("1. 📱 Enter the OTP code in the browser form")
            print("2. 🔘 Click 'Verify' or 'Submit'")
            print("3. ✅ Wait for successful login")
            print("\nPress ENTER here when you're successfully logged in...")
            print("="*55)
            
            input("Press ENTER after completing OTP entry: ")
            
            # Check if login was successful
            print("\n🔍 Verifying login status...")
            await asyncio.sleep(2)
            
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            # More thorough login check
            if 'login' not in current_url.lower():
                print("✅ Login appears successful!")
                
                # Check if we can access booking page
                try:
                    await page.goto('https://booking.gopichandacademy.com/venue-details/1', wait_until="networkidle")
                    await asyncio.sleep(3)
                    
                    # Check if we can see booking elements
                    booking_elements = await page.query_selector_all('.court, [class*="court"], .booking, [class*="booking"]')
                    if booking_elements:
                        print(f"✅ Found {len(booking_elements)} booking elements on page")
                    else:
                        print("⚠️ No booking elements found - may need to navigate differently")
                        
                except Exception as e:
                    print(f"⚠️ Error accessing booking page: {e}")
                
                # Now proceed with slot checking
                print("\n🏸 Starting comprehensive slot check...")
                
                # Get academies configuration from config
                academies_to_check = config.get_academies_to_check()
                academies = {k: v for k, v in config.academies.items() if k in academies_to_check}
                
                print(f"🏟️ Checking {len(academies)} academies:")
                for academy_key, academy_info in academies.items():
                    print(f"   • {academy_info['name']}")
                
                # Check each academy properly
                all_available_slots = await booking_checker.get_all_available_slots(
                    page, 
                    academies, 
                    dates_to_check, 
                    config.rate_limiting
                )
                
                # Send results with detailed info
                if all_available_slots:
                    print(f"\n🎉 SUCCESS! Found {len(all_available_slots)} available slots!")
                    
                    # Group slots by academy
                    academy_slots = {}
                    for slot in all_available_slots:
                        academy = slot.get('academy', 'Unknown')
                        if academy not in academy_slots:
                            academy_slots[academy] = []
                        academy_slots[academy].append(slot)
                    
                    # Display results by academy
                    print("\n📋 Available Slots by Academy:")
                    for academy, slots in academy_slots.items():
                        print(f"\n🏟️ {academy} ({len(slots)} slots):")
                        for slot in slots[:5]:  # Show first 5 slots per academy
                            print(f"   📅 {slot.get('date', 'N/A')} - Court {slot.get('court', 'N/A')} - {slot.get('time', 'N/A')}")
                        if len(slots) > 5:
                            print(f"   ... and {len(slots) - 5} more slots")
                    
                    # Send Telegram notification
                    try:
                        await notification.send_slot_notifications(all_available_slots)
                        print("\n📱 Telegram notification sent with all slot details!")
                    except Exception as e:
                        print(f"\n❌ Failed to send notification: {e}")
                        
                else:
                    print("\n😔 No available slots found at any academy")
                    print("📝 This could mean:")
                    print("   • All slots are currently booked")
                    print("   • Bookings not yet open for these dates")
                    print("   • Peak hours already filled")
                    
                    try:
                        await notification.send_slot_notifications([])
                        print("📱 'No slots available' notification sent")
                    except:
                        print("📱 Notification attempted")
                
            else:
                print("❌ Login failed. Still on login page.")
                print("🔄 Try running the script again or check your phone number")
            
            print("\n⏳ Keeping browser open for inspection (10 seconds)...")
            await asyncio.sleep(10)
            await browser.close()
            
        print(f"\n✅ Check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔄 Run this script regularly to catch newly available slots!")
        
    except Exception as e:
        print(f"\n❌ Error during check: {e}")
        print("🔍 Common issues:")
        print("   • Internet connection problems")
        print("   • Website temporarily unavailable")  
        print("   • Phone number format issues")

if __name__ == "__main__":
    asyncio.run(improved_slot_checker())
