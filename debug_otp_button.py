import asyncio
from playwright.async_api import async_playwright

async def debug_otp_button():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate and click login
            print('🌐 Going to website...')
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle")
            await asyncio.sleep(5)
            
            print('🔗 Clicking Login...')
            login_btn = await page.wait_for_selector('span:has-text("Login")', timeout=10000)
            await login_btn.click()
            await asyncio.sleep(3)
            
            print('📱 Entering phone number...')
            phone_input = await page.wait_for_selector('input', timeout=10000)
            await phone_input.click()
            await phone_input.fill('')
            await phone_input.type('+916260210006')
            await asyncio.sleep(2)
            
            print('🔘 Looking for buttons after entering phone...')
            buttons = await page.query_selector_all('button, [role="button"], input[type="submit"], .btn, [class*="button"]')
            
            for i, button in enumerate(buttons):
                try:
                    text = await button.inner_text()
                    tag_name = await button.evaluate('el => el.tagName.toLowerCase()')
                    button_type = await button.get_attribute('type')
                    class_name = await button.get_attribute('class')
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    print(f'  Button {i+1}: {tag_name} - "{text}" (type={button_type}, class={class_name})')
                    print(f'            visible={is_visible}, enabled={is_enabled}')
                    
                    # Try clicking any button that might be the OTP button
                    if text and ('otp' in text.lower() or 'send' in text.lower() or 'submit' in text.lower()):
                        print(f'    💡 This looks like an OTP button!')
                        
                except Exception as e:
                    print(f'  Button {i+1}: Error analyzing - {e}')
            
            # Look for any clickable elements
            print('🔍 Other clickable elements:')
            clickables = await page.query_selector_all('*[onclick], a, [role="button"]')
            for i, elem in enumerate(clickables[:10]):  # First 10 only
                try:
                    text = await elem.inner_text()
                    tag_name = await elem.evaluate('el => el.tagName.toLowerCase()')
                    if text and text.strip():
                        print(f'  Clickable {i+1}: {tag_name} - "{text.strip()[:50]}"')
                except:
                    continue
                    
        except Exception as e:
            print(f'❌ Error: {e}')
        
        print('⏳ Keeping browser open for inspection (15 seconds)...')
        await asyncio.sleep(15)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_otp_button())
