#!/usr/bin/env python3
"""
Test the updated modal-based login approach
"""

import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_modal_login():
    """Test the modal-based login approach with actual HTML structure"""
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720}
            )
            page = await context.new_page()
            
            # Navigate to main SPA page
            logger.info("🌐 Navigating to main SPA page...")
            await page.goto('https://booking.gopichandacademy.com/', 
                           wait_until='networkidle', timeout=30000)
            
            title = await page.title()
            logger.info(f"📄 Page loaded - Title: '{title}'")
            
            # Wait for React SPA to initialize
            await asyncio.sleep(5)
            
            # Look for the Login/SignUp button
            logger.info("🔍 Looking for 'Login / SignUp' button...")
            
            # Try clicking the login button using different strategies
            login_clicked = False
            
            # Strategy 1: Click by class
            try:
                login_btn = await page.query_selector('.login-btn')
                if login_btn:
                    logger.info("✅ Found login button by class '.login-btn'")
                    await login_btn.click()
                    await asyncio.sleep(3)
                    
                    # Check if modal appeared
                    modal = await page.query_selector('.modal-overlay')
                    if modal:
                        logger.info("🎯 Modal appeared after clicking login button!")
                        login_clicked = True
                    else:
                        logger.info("⚠️ Modal didn't appear")
                        
            except Exception as e:
                logger.info(f"⚠️ Strategy 1 failed: {e}")
            
            # Strategy 2: Click by text content if modal didn't appear
            if not login_clicked:
                try:
                    # Look for text containing "Login"
                    elements = await page.query_selector_all('span, div')
                    for element in elements:
                        text = await element.inner_text()
                        if 'Login' in text and 'SignUp' in text:
                            logger.info(f"🎯 Found element with login text: '{text}'")
                            await element.click()
                            await asyncio.sleep(3)
                            
                            modal = await page.query_selector('.modal-overlay')
                            if modal:
                                logger.info("🎯 Modal appeared after text click!")
                                login_clicked = True
                                break
                                
                except Exception as e:
                    logger.info(f"⚠️ Strategy 2 failed: {e}")
            
            # Check modal content if it appeared
            if login_clicked:
                logger.info("📋 Analyzing modal content...")
                
                modal = await page.query_selector('.modal-overlay')
                if modal:
                    # Look for the mobile input field
                    mobile_input = await page.query_selector('#mobile')
                    if mobile_input:
                        logger.info("✅ Found mobile input field with ID 'mobile'")
                        
                        # Check input attributes
                        placeholder = await mobile_input.get_attribute('placeholder')
                        maxlength = await mobile_input.get_attribute('maxlength')
                        input_type = await mobile_input.get_attribute('type')
                        logger.info(f"📝 Mobile input - Type: '{input_type}', Placeholder: '{placeholder}', MaxLength: '{maxlength}'")
                        
                        # Try filling with test number
                        await mobile_input.fill("1234567890")
                        logger.info("📝 Filled mobile input with test number")
                        
                        # Look for Send OTP button
                        otp_button = await page.query_selector('input[value="Send OTP"]')
                        if not otp_button:
                            otp_button = await page.query_selector('.custom-button')
                        
                        if otp_button:
                            logger.info("✅ Found Send OTP button")
                            button_value = await otp_button.get_attribute('value')
                            button_class = await otp_button.get_attribute('class')
                            logger.info(f"🔘 OTP Button - Value: '{button_value}', Class: '{button_class}'")
                            
                            # Don't actually click - just verify it's there
                            logger.info("🎯 Login flow verified - modal and form elements found!")
                            
                        else:
                            logger.error("❌ Send OTP button not found")
                    else:
                        logger.error("❌ Mobile input field not found in modal")
                        
                        # Debug: show all inputs in modal
                        modal_inputs = await modal.query_selector_all('input')
                        logger.info(f"🔍 Found {len(modal_inputs)} inputs in modal:")
                        for i, inp in enumerate(modal_inputs):
                            inp_id = await inp.get_attribute('id') or 'no-id'
                            inp_type = await inp.get_attribute('type') or 'no-type'
                            inp_placeholder = await inp.get_attribute('placeholder') or 'no-placeholder'
                            logger.info(f"  Input {i+1}: id='{inp_id}', type='{inp_type}', placeholder='{inp_placeholder}'")
                else:
                    logger.error("❌ Modal overlay not found")
            else:
                logger.error("❌ Could not open login modal")
            
            # Take final screenshot
            await page.screenshot(path='data/modal_test_result.png', full_page=True)
            logger.info("📸 Screenshot saved: data/modal_test_result.png")
            
            # Keep browser open for inspection
            logger.info("🔍 Browser will stay open for 20 seconds...")
            await asyncio.sleep(20)
            
            await browser.close()
            return login_clicked
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_modal_login())
    if success:
        logger.info("✅ Modal login flow works!")
    else:
        logger.error("❌ Modal login flow failed")
