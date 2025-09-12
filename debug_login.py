import asyncio
from playwright.async_api import async_playwright

async def debug_login_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        print('🔍 Navigating to login page...')
        await page.goto('https://booking.gopichandacademy.com/login', wait_until='networkidle')
        
        # Take screenshot for debugging
        await page.screenshot(path='../data/login_page_debug.png')
        print('📷 Screenshot saved to data/login_page_debug.png')
        
        # Check what elements are actually on the page
        print('🔎 Looking for input elements...')
        inputs = await page.query_selector_all('input')
        for i, input_elem in enumerate(inputs):
            input_type = await input_elem.get_attribute('type')
            input_name = await input_elem.get_attribute('name')
            input_id = await input_elem.get_attribute('id')
            input_placeholder = await input_elem.get_attribute('placeholder')
            print(f'  Input {i}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}')
        
        # Check for phone-related selectors
        phone_selectors = [
            'input[type="tel"]',
            'input[name="phone"]',
            'input[name="mobile"]',
            'input[name="phoneNumber"]',
            'input[placeholder*="phone"]',
            'input[placeholder*="mobile"]',
            'input[placeholder*="number"]'
        ]
        
        print('📱 Checking phone number selectors...')
        for selector in phone_selectors:
            element = await page.query_selector(selector)
            if element:
                print(f'  ✅ Found: {selector}')
            else:
                print(f'  ❌ Not found: {selector}')
        
        # Get page content for analysis
        title = await page.title()
        print(f'📄 Page title: {title}')
        
        # Check if the page structure changed
        print('🌐 Checking page content...')
        body_text = await page.inner_text('body')
        if 'phone' in body_text.lower():
            print('✅ Found "phone" in page content')
        if 'mobile' in body_text.lower():
            print('✅ Found "mobile" in page content')
        if 'login' in body_text.lower():
            print('✅ Found "login" in page content')
        
        # Wait a bit to see the page
        print('⏳ Waiting 10 seconds for manual inspection...')
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_login_page())
