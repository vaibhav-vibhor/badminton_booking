import asyncio
import os
from playwright.async_api import async_playwright

async def comprehensive_login_debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser so we can see
        context = await browser.new_context()
        page = await context.new_page()
        
        print('🌐 Navigating to the booking website...')
        
        try:
            # Try the main page first
            await page.goto('https://booking.gopichandacademy.com/', wait_until='networkidle')
            print(f'📄 Main page title: {await page.title()}')
            
            # Wait for any dynamic content to load
            await asyncio.sleep(3)
            
            # Look for login-related links/buttons
            print('🔍 Looking for login elements on main page...')
            
            # Check for various login-related selectors
            login_selectors = [
                'a[href*="login"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'a:has-text("Login")',
                'a:has-text("Sign In")',
                '.login',
                '#login',
                '[data-testid*="login"]'
            ]
            
            login_element = None
            for selector in login_selectors:
                element = await page.query_selector(selector)
                if element:
                    print(f'✅ Found login element: {selector}')
                    login_element = element
                    break
            
            # If we found a login element, click it
            if login_element:
                print('🔗 Clicking login element...')
                await login_element.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
            else:
                # Try going directly to login page
                print('🔗 Trying direct login page...')
                await page.goto('https://booking.gopichandacademy.com/login', wait_until='networkidle')
                await asyncio.sleep(3)
            
            print(f'📄 Current page title: {await page.title()}')
            print(f'🌐 Current URL: {page.url}')
            
            # Now look for ALL input fields
            print('📝 All input fields on the page:')
            inputs = await page.query_selector_all('input')
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute('type') or 'text'
                input_name = await input_elem.get_attribute('name') or 'unnamed'
                input_id = await input_elem.get_attribute('id') or 'no-id'
                input_placeholder = await input_elem.get_attribute('placeholder') or 'no-placeholder'
                input_class = await input_elem.get_attribute('class') or 'no-class'
                
                print(f'  Input {i+1}: type="{input_type}", name="{input_name}", id="{input_id}"')
                print(f'           placeholder="{input_placeholder}", class="{input_class}"')
            
            # Look for buttons
            print('🔘 All buttons on the page:')
            buttons = await page.query_selector_all('button')
            for i, button in enumerate(buttons):
                button_text = await button.inner_text()
                button_type = await button.get_attribute('type') or 'button'
                button_class = await button.get_attribute('class') or 'no-class'
                print(f'  Button {i+1}: text="{button_text}", type="{button_type}", class="{button_class}"')
            
            # Get page HTML content (first 1000 chars for debugging)
            content = await page.content()
            print(f'📰 Page content preview (first 500 chars):')
            print(content[:500])
            print('...')
            
            # Take screenshot
            screenshot_path = os.path.join('data', 'current_page_debug.png')
            await page.screenshot(path=screenshot_path)
            print(f'📷 Screenshot saved to {screenshot_path}')
            
        except Exception as e:
            print(f'❌ Error during debugging: {e}')
        
        print('⏳ Keeping browser open for 15 seconds for manual inspection...')
        await asyncio.sleep(15)
        
        await browser.close()
        print('✅ Debug complete')

if __name__ == "__main__":
    asyncio.run(comprehensive_login_debug())
