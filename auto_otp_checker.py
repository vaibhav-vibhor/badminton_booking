#!/usr/bin/env python3
"""
Badminton Checker - Auto Send OTP + Manual OTP Entry
This version automatically sends OTP and pauses for manual OTP entry
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from playwright.async_api import async_playwright
from config_handler import ConfigHandler
from notification_handler import NotificationHandler
from booking_checker import BookingChecker

async def auto_send_otp_checker():
    """Run slot checker with auto Send OTP + manual OTP entry"""
    
    print("🏸 Badminton Slot Checker - Auto Send OTP Mode")
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
        
        async with async_playwright() as p:
            # Launch browser (visible for manual OTP entry)
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🌐 Navigating to booking website...")
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
                print("📤 Send OTP button clicked! OTP should be sent to your phone.")
                await asyncio.sleep(3)
            else:
                print("❌ Send OTP button not found. Please click it manually.")
            
            # Manual OTP entry
            print("\n" + "="*55)
            print("📱 CHECK YOUR PHONE FOR OTP!")
            print("="*55)
            print("The OTP has been sent to your phone number:")
            print(f"   📞 {config.phone_number}")
            print()
            print("Please complete these steps in the browser window:")
            print("1. ✅ OTP has been sent (done automatically)")
            print("2. 📱 Check your SMS for the OTP code")
            print("3. ⌨️  Enter the OTP code in the form")
            print("4. 🔘 Click 'Verify' or 'Submit'")
            print("5. ✅ Complete any additional login steps")
            print("\nPress ENTER here when you're successfully logged in...")
            print("="*55)
            
            input("Press ENTER after completing OTP entry: ")
            
            # Check if login was successful
            print("\n🔍 Checking if login was successful...")
            await asyncio.sleep(2)
            
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            if 'login' not in current_url.lower():
                print("✅ Login appears successful!")
                
                # Now proceed with slot checking
                print("\n🏸 Starting slot availability check...")
                
                dates_to_check = [
                    "2025-09-13", "2025-09-14", "2025-09-15", 
                    "2025-09-16", "2025-09-17", "2025-09-18"
                ]
                
                # Get academies configuration from config
                academies_to_check = config.get_academies_to_check()
                academies = {k: v for k, v in config.academies.items() if k in academies_to_check}
                all_available_slots = []
                
                # Check each academy properly
                all_available_slots = await booking_checker.get_all_available_slots(
                    page, 
                    academies, 
                    dates_to_check, 
                    config.rate_limiting
                )
                
                # Send results
                if all_available_slots:
                    print(f"\n🎉 Found {len(all_available_slots)} total available slots!")
                    
                    # Send Telegram notification
                    try:
                        await notification.send_slot_notifications(all_available_slots)
                        print("📱 Telegram notification sent!")
                    except Exception as e:
                        print(f"❌ Failed to send notification: {e}")
                        
                    # Display results
                    print("\n📋 Available Slots:")
                    for slot in all_available_slots:
                        print(f"  🏟️ {slot['academy']} - {slot['date']} - Court {slot['court']} - {slot['time']}")
                        
                else:
                    print("\n😔 No available slots found at any academy")
                    try:
                        await notification.send_slot_notifications([])
                        print("📱 'No slots available' notification sent")
                    except:
                        print("📱 Notification attempted")
                
            else:
                print("❌ Login may not have been successful. Still on login page.")
                try:
                    await notification.send_slot_notifications([])
                except:
                    print("📱 Login failed notification attempted")
            
            print("\n⏳ Keeping browser open for 5 seconds...")
            await asyncio.sleep(5)
            await browser.close()
            
        print(f"\n✅ Check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error during check: {e}")
        try:
            notification = NotificationHandler(config.telegram_bot_token, config.telegram_chat_id)
            await notification.send_slot_notifications([])
        except:
            print("📱 Error notification attempted")

if __name__ == "__main__":
    asyncio.run(auto_send_otp_checker())
