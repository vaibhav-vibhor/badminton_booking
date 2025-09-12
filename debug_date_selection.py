import asyncio
from playwright.async_api import async_playwright

async def debug_date_selection():
    """Debug what happens when we select a date"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Load environment variables for login
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        phone_number = os.getenv('PHONE_NUMBER')
        
        try:
            print("🔍 Starting date selection debug...")
            
            # Go to login page first
            await page.goto('https://booking.gopichandacademy.com/login', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Click Login button first
            print("📱 Looking for Login button...")
            login_selectors = ['button:has-text("Login")', 'input[value="Login"]', '.custom-button', 'button[type="submit"]']
            
            for selector in login_selectors:
                try:
                    login_element = await page.query_selector(selector)
                    if login_element:
                        print(f"   Found Login button with selector: {selector}")
                        await login_element.click()
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # Enter phone number
            print("📞 Looking for phone input...")
            phone_selectors = [
                'input[type="tel"]',
                'input[name*="phone"]',
                'input[name*="mobile"]',
                'input[placeholder*="phone"]',
                'input[placeholder*="mobile"]',
                'input[placeholder*="number"]'
            ]
            
            phone_input = None
            for selector in phone_selectors:
                try:
                    phone_input = await page.wait_for_selector(selector, timeout=3000)
                    if phone_input:
                        print(f"   Found phone input with: {selector}")
                        break
                except:
                    continue
            
            if not phone_input:
                print("❌ Could not find phone input field")
                return
                
            await phone_input.fill(phone_number)
            await asyncio.sleep(1)
            
            # Click Send OTP
            print("🔐 Looking for Send OTP button...")
            send_otp_selectors = ['.custom-button', 'button:has-text("Send")', 'input[value*="Send"]']
            
            for selector in send_otp_selectors:
                try:
                    send_otp_button = await page.wait_for_selector(selector, timeout=3000)
                    if send_otp_button:
                        print(f"   Found Send OTP button with: {selector}")
                        await send_otp_button.click()
                        break
                except:
                    continue
            
            print("⏳ Please enter OTP manually in the browser and complete login...")
            print("   Once logged in and redirected, press Enter here to continue...")
            input("   Press Enter when ready...")
            
            # Go to Kotak academy page
            kotak_url = "https://booking.gopichandacademy.com/booking/facility/kotak-pullela-gopichand--badminton-academy"
            print(f"🏸 Navigating to: {kotak_url}")
            await page.goto(kotak_url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Take screenshot before date selection
            await page.screenshot(path='data/before_date_selection.png')
            print("📸 Screenshot saved: data/before_date_selection.png")
            
            # Check current availability section
            print("🔍 Checking availability section before date selection...")
            availability_section = await page.query_selector('div.form-group:has(label:text("Availability:"))')
            if availability_section:
                availability_content = await availability_section.inner_text()
                print(f"   Availability content: {availability_content}")
            
            # Find date input
            print("📅 Looking for date input...")
            date_input = await page.wait_for_selector('input#card1[type="date"]', timeout=10000)
            print("   Found date input")
            
            # Set tomorrow's date (2025-09-13)
            target_date = "2025-09-13"
            print(f"   Setting date to: {target_date}")
            await date_input.fill(target_date)
            await asyncio.sleep(2)
            
            # Trigger change event
            await date_input.dispatch_event('change')
            await asyncio.sleep(3)
            
            # Take screenshot after date selection  
            await page.screenshot(path='data/after_date_selection.png')
            print("📸 Screenshot saved: data/after_date_selection.png")
            
            # Check what changed in availability section
            print("🔍 Checking availability section after date selection...")
            availability_section = await page.query_selector('div.form-group:has(label:text("Availability:"))')
            if availability_section:
                availability_content = await availability_section.inner_text()
                print(f"   Availability content: {availability_content}")
            
            # Look for court elements with different selectors
            court_selectors = [
                'div.court-item',
                'div.court',  
                'button[data-court]',
                'div[class*="court"]',
                'div.grid--area div',
                'div.flex-container div',
                'div.flex-container > *',
                '.grid--area > *'
            ]
            
            print("🏟️ Looking for courts with various selectors...")
            for selector in court_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"   Found {len(elements)} elements with selector: {selector}")
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            text = await elem.inner_text() 
                            if text.strip():
                                print(f"      Element {i}: {text.strip()[:50]}")
                    else:
                        print(f"   No elements found with: {selector}")
                except:
                    print(f"   Error with selector: {selector}")
            
            # Check the grid area specifically
            print("🔍 Checking grid area content...")
            grid_area = await page.query_selector('div.grid--area.flex-container')
            if grid_area:
                grid_content = await grid_area.inner_html()
                print(f"   Grid area HTML: {grid_content[:200]}...")
                
                # Look for any clickable elements in grid
                clickable_elements = await grid_area.query_selector_all('div, button, span, a')
                print(f"   Found {len(clickable_elements)} clickable elements in grid")
                for i, elem in enumerate(clickable_elements[:5]):
                    text = await elem.inner_text()
                    if text.strip():
                        print(f"      Clickable {i}: {text.strip()}")
            
            print("⏳ Waiting 10 seconds for manual inspection...")
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_date_selection())
