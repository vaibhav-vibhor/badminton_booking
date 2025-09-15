#!/usr/bin/env python3
"""
Debug script to check the current login page structure
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_login_page():
    """Check what the login page currently looks like"""
    async with async_playwright() as playwright:
        # Launch browser in headless mode (like GitHub Actions)
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            logger.info("🌐 Navigating to login page...")
            await page.goto('https://booking.gopichandacademy.com/login', 
                           wait_until='networkidle', timeout=30000)
            await asyncio.sleep(5)
            
            # Take full page screenshot
            await page.screenshot(path='data/current_login_page.png', full_page=True)
            logger.info("📸 Screenshot saved as current_login_page.png")
            
            # Get page title and URL
            title = await page.title()
            url = page.url
            logger.info(f"📄 Page title: {title}")
            logger.info(f"🔗 Current URL: {url}")
            
            # Check for phone input fields
            logger.info("🔍 Checking for phone input elements...")
            phone_selectors = [
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="mobile"]',
                'input[name="phoneNumber"]',
                'input[placeholder*="phone" i]',
                'input[placeholder*="mobile" i]',
                'input[placeholder*="number" i]',
                'input[type="text"]',  # Check all text inputs too
                'input[type="email"]'  # Check if they changed to email login
            ]
            
            found_inputs = []
            for selector in phone_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} element(s) for: {selector}")
                        for i, element in enumerate(elements):
                            # Get element attributes
                            name = await element.get_attribute('name') or 'no-name'
                            placeholder = await element.get_attribute('placeholder') or 'no-placeholder'
                            id_attr = await element.get_attribute('id') or 'no-id'
                            type_attr = await element.get_attribute('type') or 'no-type'
                            found_inputs.append(f"  #{i+1}: type={type_attr}, name={name}, id={id_attr}, placeholder={placeholder}")
                except Exception as e:
                    logger.debug(f"Error checking {selector}: {e}")
            
            if found_inputs:
                logger.info("📝 Found input elements:")
                for input_info in found_inputs:
                    logger.info(input_info)
            else:
                logger.warning("⚠️ No input elements found!")
            
            # Get page content for analysis
            page_content = await page.content()
            logger.info(f"📄 Page content length: {len(page_content)} characters")
            
            # Check for specific text that might indicate what type of login page this is
            if 'phone' in page_content.lower():
                logger.info("✅ Page mentions 'phone'")
            if 'email' in page_content.lower():
                logger.info("✅ Page mentions 'email'")
            if 'login' in page_content.lower():
                logger.info("✅ Page mentions 'login'")
            if 'otp' in page_content.lower():
                logger.info("✅ Page mentions 'OTP'")
                
        except Exception as e:
            logger.error(f"❌ Error during debug: {e}")
            await page.screenshot(path='data/error_page.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_login_page())
