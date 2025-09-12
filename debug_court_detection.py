import asyncio
from playwright.async_api import async_playwright

async def debug_court_detection():
    """Debug court detection after date selection"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🔍 Court detection debug - Please complete login manually first...")
            
            # Go directly to Kotak academy page
            kotak_url = "https://booking.gopichandacademy.com/booking/facility/kotak-pullela-gopichand--badminton-academy"
            print(f"🏸 Please login first, then navigate to: {kotak_url}")
            print("   Once on the academy page, press Enter here to continue...")
            input("   Press Enter when ready...")
            
            # Wait for user to navigate
            await asyncio.sleep(2)
            
            # Take screenshot of initial state
            await page.screenshot(path='data/court_debug_initial.png')
            print("📸 Initial screenshot: data/court_debug_initial.png")
            
            # Check current page content
            print("🔍 Checking current page content...")
            try:
                # Look for the date input
                date_input = await page.query_selector('input#card1[type="date"]')
                if date_input:
                    print("   ✅ Found date input")
                    current_value = await date_input.get_attribute('value')
                    print(f"   Current date value: {current_value}")
                else:
                    print("   ❌ Date input not found")
                    return
                
                # Check availability section content
                availability_section = await page.query_selector('div.form-group:has(label:text("Availability:"))')
                if availability_section:
                    content = await availability_section.inner_text()
                    print(f"   Availability section: {content.strip()}")
                
                # Try different dates
                test_dates = ["2025-09-13", "2025-09-14", "2025-09-15"]
                
                for test_date in test_dates:
                    print(f"\n📅 Testing date: {test_date}")
                    
                    # Set the date
                    await date_input.fill(test_date)
                    await asyncio.sleep(1)
                    
                    # Trigger change event
                    await date_input.dispatch_event('change')
                    await asyncio.sleep(3)  # Wait for page to load
                    
                    # Take screenshot after date change
                    await page.screenshot(path=f'data/court_debug_{test_date}.png')
                    print(f"   📸 Screenshot: data/court_debug_{test_date}.png")
                    
                    # Check availability section again
                    availability_section = await page.query_selector('div.form-group:has(label:text("Availability:"))')
                    if availability_section:
                        content = await availability_section.inner_text()
                        print(f"   Availability: {content.strip()}")
                        
                        # Look for court elements within availability section
                        court_elements = await availability_section.query_selector_all('div, button, span')
                        print(f"   Found {len(court_elements)} elements in availability section")
                        
                        for i, elem in enumerate(court_elements[:10]):
                            try:
                                text = await elem.inner_text()
                                if text.strip() and len(text.strip()) > 1:
                                    print(f"      Element {i}: {text.strip()[:100]}")
                            except:
                                pass
                    
                    # Check the grid area specifically  
                    grid_area = await page.query_selector('div.grid--area.flex-container')
                    if grid_area:
                        grid_html = await grid_area.inner_html()
                        print(f"   Grid HTML length: {len(grid_html)} chars")
                        if len(grid_html) > 50:  # If there's actual content
                            print(f"   Grid content preview: {grid_html[:200]}...")
                            
                            # Look for clickable elements
                            clickable = await grid_area.query_selector_all('div, button, span, a')
                            print(f"   Clickable elements in grid: {len(clickable)}")
                            
                            for i, elem in enumerate(clickable[:5]):
                                try:
                                    text = await elem.inner_text()
                                    if text.strip():
                                        print(f"      Clickable {i}: {text.strip()}")
                                except:
                                    pass
                    
                    # Check time slots container
                    time_container = await page.query_selector('div.time-slots-container')
                    if time_container:
                        time_content = await time_container.inner_text()
                        print(f"   Time slots: {time_content.strip()}")
                    
                    print(f"   ⏳ Waiting 5 seconds before next date...")
                    await asyncio.sleep(5)
                
                print("\n✅ Debug complete! Check the screenshots to see what's happening.")
                
            except Exception as e:
                print(f"❌ Error during debugging: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            print("Closing browser in 10 seconds...")
            await asyncio.sleep(10)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_court_detection())
