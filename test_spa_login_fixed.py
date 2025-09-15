#!/usr/bin/env python3
"""
Test the updated SPA login approach
"""

import asyncio
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_spa_login():
    """Test the updated SPA login approach"""
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # Navigate to main SPA page (not /login which returns 404)
            logger.info("🌐 Navigating to main SPA page...")
            await page.goto('https://booking.gopichandacademy.com/', 
                           wait_until='networkidle', timeout=30000)
            
            # Log page info after navigation
            title = await page.title()
            url = page.url
            logger.info(f"📄 Page loaded - Title: '{title}', URL: '{url}'")
            
            # Wait for React SPA to initialize
            logger.info("⏳ Waiting for React SPA to initialize...")
            await asyncio.sleep(5)
            
            # Try to find login button/link in the SPA
            logger.info("🔍 Looking for login button/link in SPA...")
            login_found = False
            login_selectors = [
                'button:has-text("Login")',
                'button:has-text("Sign In")', 
                'button:has-text("Log In")',
                'a:has-text("Login")',
                'a:has-text("Sign In")',
                'a:has-text("Log In")',
                '[role="button"]:has-text("Login")',
                '[role="button"]:has-text("Sign In")',
                'button[class*="login" i]',
                'a[class*="login" i]',
                'button[id*="login" i]',
                'a[id*="login" i]'
            ]
            
            for selector in login_selectors:
                try:
                    login_element = await page.query_selector(selector)
                    if login_element:
                        logger.info(f"🎯 Found login element with selector: {selector}")
                        text = await login_element.inner_text()
                        logger.info(f"📝 Element text: '{text}'")
                        
                        # Click the login button/link
                        await login_element.click()
                        logger.info("👆 Clicked login element")
                        
                        # Wait for navigation or modal to appear
                        await asyncio.sleep(3)
                        login_found = True
                        break
                except Exception as e:
                    logger.debug(f"⚠️ Selector {selector} failed: {e}")
            
            # If no login button found, look for any clickable elements
            if not login_found:
                logger.info("🔍 No login button found, analyzing all clickable elements...")
                buttons = await page.query_selector_all('button, a, [role="button"]')
                logger.info(f"🔘 Found {len(buttons)} clickable elements")
                
                for i, button in enumerate(buttons[:10]):  # Check first 10
                    try:
                        text = await button.inner_text()
                        tag_name = await button.evaluate('el => el.tagName')
                        classes = await button.get_attribute('class') or ''
                        href = await button.get_attribute('href') or ''
                        logger.info(f"Button {i+1}: <{tag_name.lower()}> text='{text[:50]}' class='{classes[:50]}' href='{href[:50]}'")
                    except Exception:
                        pass
            
            # Try SPA routing approaches
            if not login_found:
                logger.info("🔄 Trying SPA routing approaches...")
                
                # Try hash-based routing
                hash_routes = ['#/login', '#login', '#/signin', '#signin', '#/auth']
                for route in hash_routes:
                    try:
                        new_url = 'https://booking.gopichandacademy.com/' + route
                        logger.info(f"🔗 Trying hash route: {new_url}")
                        await page.goto(new_url, wait_until='networkidle', timeout=10000)
                        await asyncio.sleep(3)
                        
                        # Check if login form appeared
                        inputs = await page.query_selector_all('input')
                        if inputs:
                            logger.info(f"✅ Found {len(inputs)} inputs after navigating to {route}")
                            for j, inp in enumerate(inputs[:5]):
                                inp_type = await inp.get_attribute('type') or 'text'
                                placeholder = await inp.get_attribute('placeholder') or ''
                                logger.info(f"  Input {j+1}: type='{inp_type}', placeholder='{placeholder}'")
                            login_found = True
                            break
                    except Exception as e:
                        logger.info(f"⚠️ Hash route {route} failed: {str(e)[:100]}")
                
                # Try history API routing if hash routing didn't work
                if not login_found:
                    history_routes = ['/login', '/signin', '/auth', '/user/login']
                    for route in history_routes:
                        try:
                            new_url = 'https://booking.gopichandacademy.com' + route
                            logger.info(f"🔗 Trying history route: {new_url}")
                            await page.goto(new_url, wait_until='networkidle', timeout=10000)
                            await asyncio.sleep(3)
                            
                            # Check if login form appeared
                            inputs = await page.query_selector_all('input')
                            if inputs:
                                logger.info(f"✅ Found {len(inputs)} inputs after navigating to {route}")
                                for j, inp in enumerate(inputs[:5]):
                                    inp_type = await inp.get_attribute('type') or 'text'
                                    placeholder = await inp.get_attribute('placeholder') or ''
                                    logger.info(f"  Input {j+1}: type='{inp_type}', placeholder='{placeholder}'")
                                login_found = True
                                break
                        except Exception as e:
                            logger.info(f"⚠️ History route {route} failed: {str(e)[:100]}")
            
            # Final check for any inputs on current page
            final_inputs = await page.query_selector_all('input')
            logger.info(f"📝 Final input count: {len(final_inputs)}")
            
            # Take screenshots for manual inspection
            current_url = page.url
            logger.info(f"📍 Final URL: {current_url}")
            
            screenshot_path = f'data/spa_test_final.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Keep browser open for manual inspection
            logger.info("🔍 Browser will stay open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            
            await browser.close()
            
            return login_found
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_spa_login())
    if success:
        logger.info("✅ Login interface found!")
    else:
        logger.info("❌ No login interface found - may need manual inspection")
