#!/usr/bin/env python3
"""
Local test script to debug the login page structure
"""

import asyncio
import logging
import sys
import os
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_login_page():
    """Test the login page structure locally"""
    async with async_playwright() as playwright:
        # Launch browser in headed mode so we can see what's happening
        browser = await playwright.chromium.launch(
            headless=False,  # Show the browser so we can see
            slow_mo=1000  # Slow down actions
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            logger.info("🌐 Navigating to login page...")
            await page.goto('https://booking.gopichandacademy.com/login', 
                           wait_until='networkidle', timeout=30000)
            
            # Log page info after navigation
            title = await page.title()
            url = page.url
            logger.info(f"📄 Page loaded - Title: '{title}', URL: '{url}'")
            
            # Wait longer for dynamic content to load
            logger.info("⏳ Waiting for dynamic content to load...")
            await asyncio.sleep(10)
            
            # Check if there are any scripts or dynamic content loading
            scripts = await page.query_selector_all('script')
            logger.info(f"🔧 Found {len(scripts)} script tags on page")
            
            # Check for common loading indicators
            loading_indicators = ['loading', 'spinner', 'loader']
            for indicator in loading_indicators:
                elements = await page.query_selector_all(f'[class*="{indicator}"], [id*="{indicator}"]')
                if elements:
                    logger.info(f"🔄 Found loading indicator: {indicator}")
            
            # Try waiting for any input to appear
            logger.info("🔍 Waiting for any input element to appear...")
            try:
                await page.wait_for_selector('input', timeout=15000)
                logger.info("✅ Input element appeared after waiting")
            except Exception:
                logger.warning("⚠️ No input elements appeared after 15 seconds")
            
            # Check again after waiting
            all_inputs_after_wait = await page.query_selector_all('input')
            logger.info(f"📝 Found {len(all_inputs_after_wait)} input elements after waiting")
            
            # Check for iframes that might contain the login form
            iframes = await page.query_selector_all('iframe')
            logger.info(f"🖼️ Found {len(iframes)} iframe(s) on page")
            
            if iframes:
                for i, iframe in enumerate(iframes):
                    try:
                        frame = await iframe.content_frame()
                        if frame:
                            frame_inputs = await frame.query_selector_all('input')
                            logger.info(f"📝 Iframe #{i+1} contains {len(frame_inputs)} input elements")
                            if frame_inputs:
                                logger.info("🎯 Found inputs in iframe!")
                                # Show details of iframe inputs
                                for j, inp in enumerate(frame_inputs):
                                    input_type = await inp.get_attribute('type') or 'no-type'
                                    input_name = await inp.get_attribute('name') or 'no-name'
                                    input_id = await inp.get_attribute('id') or 'no-id'
                                    input_placeholder = await inp.get_attribute('placeholder') or 'no-placeholder'
                                    logger.info(f"  Iframe Input #{j+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
                    except Exception as e:
                        logger.info(f"⚠️ Could not access iframe #{i+1}: {e}")
            
            # Check what inputs are actually available on main page
            all_inputs = await page.query_selector_all('input')
            logger.info(f"📝 Main page has {len(all_inputs)} input elements:")
            
            for i, inp in enumerate(all_inputs[:10]):  # Limit to first 10
                input_type = await inp.get_attribute('type') or 'no-type'
                input_name = await inp.get_attribute('name') or 'no-name'
                input_id = await inp.get_attribute('id') or 'no-id'
                input_placeholder = await inp.get_attribute('placeholder') or 'no-placeholder'
                logger.info(f"  Input #{i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
            
            # Check for buttons that might be related to login
            buttons = await page.query_selector_all('button')
            logger.info(f"🔘 Found {len(buttons)} buttons on page")
            
            for i, btn in enumerate(buttons[:5]):  # Show first 5 buttons
                btn_text = await btn.inner_text() or 'no-text'
                btn_id = await btn.get_attribute('id') or 'no-id'
                btn_class = await btn.get_attribute('class') or 'no-class'
                logger.info(f"  Button #{i+1}: text='{btn_text}', id='{btn_id}', class='{btn_class}'")
            
            # Take screenshot for visual debugging
            await page.screenshot(path='data/local_login_debug.png', full_page=True)
            logger.info("📸 Screenshot saved as data/local_login_debug.png")
            
            # Save page content for analysis
            page_content = await page.content()
            os.makedirs('data', exist_ok=True)
            with open('data/local_login_page_content.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            logger.info("💾 Page content saved to data/local_login_page_content.html")
            
            # Keep browser open for manual inspection
            logger.info("🔍 Browser will stay open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"❌ Error during test: {e}")
            await page.screenshot(path='data/local_error_debug.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_login_page())
