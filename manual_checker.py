#!/usr/bin/env python3
"""
Badminton Checker with Manual OTP Support
This version will pause and let you complete the OTP manually
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

async def manual_otp_checker():
    """Run slot checker with manual OTP intervention"""
    
    print("🏸 Badminton Slot Checker - Manual OTP Mode")
    print("=" * 50)
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
            # Launch browser (visible for manual interaction)
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
            
            # Manual intervention point
            print("\n" + "="*50)
            print("🚨 MANUAL ACTION REQUIRED")
            print("="*50)
            print("Please complete these steps in the browser window:")
            print("1. Click the 'Send OTP' or 'Get OTP' button")
            print("2. Wait for SMS with OTP code")
            print("3. Enter the OTP code in the form")
            print("4. Click 'Verify' or 'Submit'")
            print("5. Complete any additional login steps")
            print("\nPress ENTER here when you're successfully logged in...")
            print("="*50)
            
            input("Press ENTER after completing login manually: ")
            
            # Now check if login was successful
            print("\n🔍 Checking if login was successful...")
            await asyncio.sleep(2)
            
            # Check current URL or page content to verify login
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
                
                academies = ["kotak", "pullela", "sai"]
                all_available_slots = []
                
                for academy in academies:
                    print(f"🏟️ Checking {academy.title()} Academy...")
                    
                    try:
                        slots = await booking_checker.check_academy_slots(
                            page, academy, dates_to_check, dates_to_check, True
                        )
                        
                        if slots:
                            all_available_slots.extend(slots)
                            print(f"  ✅ Found {len(slots)} available slots")
                        else:
                            print("  ❌ No slots available")
                            
                    except Exception as e:
                        print(f"  ❌ Error checking {academy}: {e}")
                
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
                    except:
                        print("📱 Notification sent: No slots available")
                
            else:
                print("❌ Login may not have been successful. Still on login page.")
                try:
                    await notification.send_slot_notifications([])
                except:
                    print("📱 Login failed notification sent")
            
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
    asyncio.run(manual_otp_checker())
