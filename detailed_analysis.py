import asyncio
from playwright.async_api import async_playwright

async def detailed_page_analysis():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        print('🌐 Loading booking website...')
        
        try:
            # Go to the main page first
            await page.goto('https://booking.gopichandacademy.com/', wait_until="networkidle", timeout=30000)
            
            # Wait for SPA to load completely
            print('⏳ Waiting for SPA to fully load (10 seconds)...')
            await asyncio.sleep(10)
            
            print(f'📄 Page title: {await page.title()}')
            print(f'🌐 Current URL: {page.url}')
            
            # Check if we need to navigate to login
            current_url = page.url
            if 'login' not in current_url.lower():
                print('🔗 Looking for login link/button...')
                
                # Look for login elements
                login_elements = await page.query_selector_all('a, button, [role="button"]')
                for element in login_elements:
                    text = await element.inner_text()
                    href = await element.get_attribute('href')
                    onclick = await element.get_attribute('onclick')
                    
                    if text and ('login' in text.lower() or 'sign in' in text.lower()):
                        print(f'  Found login element: "{text}", href={href}, onclick={onclick}')
                        try:
                            await element.click()
                            print('  Clicked login element')
                            await page.wait_for_load_state('networkidle')
                            await asyncio.sleep(5)
                            break
                        except Exception as e:
                            print(f'  Failed to click: {e}')
                            continue
            
            # Now analyze the current page
            print(f'🔍 Final URL: {page.url}')
            
            # Get all elements with text content
            print('📝 All visible elements with text:')
            elements = await page.query_selector_all('*')
            text_elements = []
            
            for element in elements[:50]:  # Limit to first 50 elements
                try:
                    text = await element.inner_text()
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    if text and text.strip():
                        text_elements.append(f'  {tag_name}: "{text.strip()[:100]}"')
                except:
                    continue
            
            for text_elem in text_elements[:20]:  # Show first 20
                print(text_elem)
            
            # Look for forms
            print('📋 Forms on page:')
            forms = await page.query_selector_all('form')
            if forms:
                for i, form in enumerate(forms):
                    form_html = await form.inner_html()
                    print(f'  Form {i+1}: {form_html[:200]}...')
            else:
                print('  No forms found')
            
            # Look for inputs again with more detail
            print('📝 All input elements:')
            inputs = await page.query_selector_all('input')
            if inputs:
                for i, input_elem in enumerate(inputs):
                    try:
                        input_type = await input_elem.get_attribute('type')
                        input_name = await input_elem.get_attribute('name')
                        input_id = await input_elem.get_attribute('id')
                        input_placeholder = await input_elem.get_attribute('placeholder')
                        input_value = await input_elem.get_attribute('value')
                        is_visible = await input_elem.is_visible()
                        
                        print(f'  Input {i+1}: type={input_type}, name={input_name}, id={input_id}')
                        print(f'           placeholder={input_placeholder}, value={input_value}, visible={is_visible}')
                    except Exception as e:
                        print(f'  Input {i+1}: Error analyzing - {e}')
            else:
                print('  No input elements found')
            
            # Take final screenshot
            await page.screenshot(path='data/final_analysis.png')
            print('📷 Screenshot saved to data/final_analysis.png')
            
        except Exception as e:
            print(f'❌ Error during analysis: {e}')
        
        print('⏳ Keeping browser open for manual inspection (20 seconds)...')
        await asyncio.sleep(20)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(detailed_page_analysis())
