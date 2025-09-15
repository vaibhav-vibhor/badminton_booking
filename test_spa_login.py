#!/usr/bin/env python3
"""
Test different approaches for SPA login detection
"""

import requests
import logging
from bs4 import BeautifulSoup
import asyncio
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_spa_login_approaches():
    """Test different ways to handle SPA login"""
    try:
        base_url = "https://booking.gopichandacademy.com"
        
        # Test if we can use Playwright to navigate to the SPA and wait for login elements
        try:
            from playwright.async_api import async_playwright
            logger.info("🎭 Testing with Playwright (full SPA support)")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False, slow_mo=1000)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Navigate to main page first
                logger.info("🌐 Navigating to main SPA page...")
                await page.goto(base_url, wait_until='networkidle', timeout=30000)
                
                # Wait for React app to fully load
                logger.info("⏳ Waiting for React app to initialize...")
                await asyncio.sleep(5)
                
                # Check if we can find any login-related elements or links
                login_keywords = ['login', 'signin', 'sign in', 'log in']
                
                for keyword in login_keywords:
                    # Look for buttons or links with login text
                    elements = await page.query_selector_all(f'button:has-text("{keyword}"), a:has-text("{keyword}"), [role="button"]:has-text("{keyword}")')
                    if elements:
                        logger.info(f"🎯 Found {len(elements)} elements with text '{keyword}'")
                        for i, element in enumerate(elements):
                            text = await element.inner_text()
                            logger.info(f"  Element {i+1}: '{text}'")
                    
                    # Look for elements with login-related classes or IDs
                    class_elements = await page.query_selector_all(f'[class*="{keyword}"], [id*="{keyword}"]')
                    if class_elements:
                        logger.info(f"🎯 Found {len(class_elements)} elements with {keyword} in class/id")
                
                # Try to find any input fields that might appear after clicking something
                all_buttons = await page.query_selector_all('button, [role="button"], a[href]')
                logger.info(f"🔘 Found {len(all_buttons)} clickable elements on page")
                
                # Look for navigation elements
                nav_elements = await page.query_selector_all('nav, [role="navigation"]')
                logger.info(f"🧭 Found {len(nav_elements)} navigation elements")
                
                for i, nav in enumerate(nav_elements):
                    nav_html = await nav.inner_html()
                    logger.info(f"Nav {i+1} HTML preview: {nav_html[:200]}...")
                
                # Try common SPA hash routes
                hash_routes = ['#/login', '#login', '#/signin', '#signin']
                for route in hash_routes:
                    test_url = base_url + route
                    logger.info(f"🔗 Testing hash route: {test_url}")
                    await page.goto(test_url, wait_until='networkidle', timeout=10000)
                    await asyncio.sleep(2)
                    
                    # Check if any input fields appeared
                    inputs = await page.query_selector_all('input')
                    if inputs:
                        logger.info(f"✅ Found {len(inputs)} input fields at {route}")
                        for j, inp in enumerate(inputs[:5]):  # Show first 5
                            inp_type = await inp.get_attribute('type') or 'text'
                            placeholder = await inp.get_attribute('placeholder') or ''
                            logger.info(f"  Input {j+1}: type='{inp_type}', placeholder='{placeholder}'")
                        break
                    else:
                        logger.info(f"❌ No input fields found at {route}")
                
                # Try to look for React Router style paths
                router_paths = ['/login', '/signin', '/auth', '/user/login']
                for path in router_paths:
                    test_url = base_url + path
                    logger.info(f"🔗 Testing router path: {test_url}")
                    try:
                        await page.goto(test_url, wait_until='networkidle', timeout=10000)
                        await asyncio.sleep(2)
                        
                        # Check if any input fields appeared
                        inputs = await page.query_selector_all('input')
                        if inputs:
                            logger.info(f"✅ Found {len(inputs)} input fields at {path}")
                            for j, inp in enumerate(inputs[:5]):
                                inp_type = await inp.get_attribute('type') or 'text'
                                placeholder = await inp.get_attribute('placeholder') or ''
                                logger.info(f"  Input {j+1}: type='{inp_type}', placeholder='{placeholder}'")
                            break
                        else:
                            logger.info(f"❌ No input fields found at {path}")
                    except Exception as e:
                        logger.info(f"❌ Error testing {path}: {str(e)[:100]}")
                
                # Take a screenshot for manual inspection
                await page.screenshot(path='data/spa_current_state.png')
                logger.info("📸 Screenshot saved as data/spa_current_state.png")
                
                # Try to execute JavaScript to find React components
                logger.info("⚛️ Looking for React components...")
                try:
                    # Check if React is loaded
                    react_version = await page.evaluate("() => window.React ? window.React.version : 'not found'")
                    logger.info(f"React version: {react_version}")
                    
                    # Try to find React Fiber node
                    fiber_info = await page.evaluate("""() => {
                        const rootElement = document.getElementById('root');
                        if (rootElement && rootElement._reactInternalFiber) {
                            return 'Found React Fiber';
                        } else if (rootElement && rootElement._reactInternals) {
                            return 'Found React Internals';
                        }
                        return 'No React found';
                    }""")
                    logger.info(f"React Fiber info: {fiber_info}")
                    
                except Exception as e:
                    logger.info(f"React detection error: {e}")
                
                await browser.close()
                
        except ImportError:
            logger.info("❌ Playwright not available, skipping browser test")
        except Exception as e:
            logger.error(f"❌ Browser test failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SPA test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_spa_login_approaches())
