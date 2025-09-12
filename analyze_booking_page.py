import asyncio
from playwright.async_api import async_playwright
import json

async def analyze_booking_page():
    """Analyze the booking page structure"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Go to Kotak academy directly (assuming logged in via cookies)
            kotak_url = "https://booking.gopichandacademy.com/booking/facility/kotak-pullela-gopichand--badminton-academy"
            print(f"🏸 Going to: {kotak_url}")
            await page.goto(kotak_url, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Save full HTML for analysis
            html_content = await page.content()
            with open('data/page_analysis.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("📄 Full HTML saved to: data/page_analysis.html")
            
            # Take screenshot
            await page.screenshot(path='data/page_analysis.png')
            print("📸 Screenshot saved to: data/page_analysis.png")
            
            # Find all form elements
            print("\n📋 FORM ANALYSIS:")
            forms = await page.query_selector_all('form')
            for i, form in enumerate(forms):
                print(f"Form {i}:")
                form_html = await form.inner_html()
                print(f"  HTML length: {len(form_html)} chars")
            
            # Find all input elements
            print("\n📝 INPUT ANALYSIS:")
            inputs = await page.query_selector_all('input')
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute('type') or 'text'
                input_name = await input_elem.get_attribute('name') or ''
                input_id = await input_elem.get_attribute('id') or ''
                input_value = await input_elem.get_attribute('value') or ''
                input_placeholder = await input_elem.get_attribute('placeholder') or ''
                print(f"  Input {i}: type={input_type}, name={input_name}, id={input_id}, value={input_value}, placeholder={input_placeholder}")
            
            # Find date input specifically
            print("\n📅 DATE INPUT ANALYSIS:")
            date_input = await page.query_selector('input[type="date"]')
            if date_input:
                print("  ✅ Found date input")
                min_date = await date_input.get_attribute('min')
                max_date = await date_input.get_attribute('max') 
                current_value = await date_input.get_attribute('value')
                print(f"     Min: {min_date}, Max: {max_date}, Current: {current_value}")
                
                # Test setting a date
                test_date = "2025-09-13"
                print(f"  📅 Setting date to: {test_date}")
                await date_input.fill(test_date)
                await asyncio.sleep(2)
                
                # Trigger events
                await date_input.dispatch_event('input')
                await date_input.dispatch_event('change')
                await asyncio.sleep(3)
                
                # Take screenshot after date change
                await page.screenshot(path='data/after_date_change.png')
                print("  📸 Screenshot after date change: data/after_date_change.png")
                
            else:
                print("  ❌ Date input not found")
            
            # Look for all div elements that might contain courts
            print("\n🏟️ POTENTIAL COURT CONTAINERS:")
            potential_containers = [
                'div.grid--area',
                'div.flex-container',
                'div[class*="court"]',
                'div[class*="slot"]',
                'div[class*="available"]',
                'div.form-group',
                '.time-slots-container'
            ]
            
            for selector in potential_containers:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"  Found {len(elements)} elements with: {selector}")
                    for i, elem in enumerate(elements[:2]):  # Show first 2
                        try:
                            text = await elem.inner_text()
                            html = await elem.inner_html()
                            print(f"    Element {i}: text='{text[:100]}...', html_len={len(html)}")
                        except:
                            pass
            
            print("\n⏳ Keeping browser open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_booking_page())
