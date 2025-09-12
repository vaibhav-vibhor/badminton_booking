import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

try:
    from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    # Fallback for when playwright is not installed
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeoutError = TimeoutError

class BookingChecker:
    """
    Handles checking badminton slot availability using the provided HTML structure
    """
    
    def __init__(self):
        # HTML selectors based on the actual HTML structure from the website
        self.selectors = {
            # Date selection
            "date_input": "input#card1[type='date']",
            "form": "form.contact-form",
            
            # Court selection (courts appear after date selection)
            "court_items": "div.court-item",
            "active_court": "div.court-item.active-court",
            "availability_container": "div.grid--area.flex-container",
            
            # Time slots (appear after court selection)
            "time_slots": "span.styled-btn",
            "time_slots_container": "div.time-slots-container",
            
            # Form submission
            "add_to_cart_button": "input.custom-button[type='submit'][value='Add to Cart']"
        }
    
    async def check_academy_slots(self, page: Any, academy_url: str, academy_name: str, target_dates: List[str], rate_limiting: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Check slot availability for a specific academy using corrected HTML selectors
        Enhanced with session management
        """
        results = []
        
        try:
            # Navigate to academy page
            logging.info(f"Checking {academy_name}...")
            await page.goto(academy_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Check if we got redirected to login page
            if 'login' in page.url.lower():
                logging.error(f"Redirected to login page when accessing {academy_name}")
                logging.error("Session may have expired - please re-run the login process")
                return []
            
            # Verify we're on the right page by looking for booking form
            try:
                await page.wait_for_selector(self.selectors["form"], timeout=10000)
                logging.info(f"Successfully accessed {academy_name} booking page")
            except PlaywrightTimeoutError:
                logging.error(f"Could not find booking form for {academy_name}")
                logging.error(f"Current URL: {page.url}")
                return []
            
            await asyncio.sleep(rate_limiting.get("delay_between_requests", 3))
            
            for date in target_dates:
                logging.info(f"Checking date: {date}")
                
                # Set the date and trigger courts to appear
                try:
                    date_input = await page.wait_for_selector(self.selectors["date_input"], timeout=5000)
                    
                    # Clear and set the date
                    await date_input.click()
                    await date_input.fill('')
                    await date_input.fill(date)
                    
                    # Trigger change events to load courts
                    await date_input.dispatch_event('input')
                    await date_input.dispatch_event('change')
                    
                    # Wait longer for courts to load after date selection
                    await asyncio.sleep(4)
                    
                except PlaywrightTimeoutError:
                    logging.error(f"Could not find date input for {academy_name}")
                    continue
                
                # Wait for courts to appear after date selection
                try:
                    await page.wait_for_selector(self.selectors["court_items"], timeout=15000)
                    court_elements = await page.query_selector_all(self.selectors["court_items"])
                    logging.info(f"Found {len(court_elements)} courts for {academy_name} on {date}")
                except PlaywrightTimeoutError:
                    logging.warning(f"No courts appeared for {academy_name} on {date} - may be outside booking window")
                    continue
                
                if not court_elements:
                    logging.warning(f"No courts found for {academy_name} on {date}")
                    continue
                
                # Check each court
                for i, court_element in enumerate(court_elements):
                    try:
                        court_number = await court_element.inner_text()
                        court_name = f"Court {court_number}"
                        logging.info(f"Checking {court_name}")
                        
                        # Click on court to select it and load time slots
                        await court_element.click()
                        await asyncio.sleep(rate_limiting.get("delay_between_courts", 3))
                        
                        # Wait for time slots to load
                        try:
                            await page.wait_for_selector(self.selectors["time_slots"], timeout=10000)
                        except PlaywrightTimeoutError:
                            logging.warning(f"No time slots loaded for {court_name}")
                            continue
                        
                        # Get time slots for this court
                        court_results = await self._check_court_slots(page, academy_name, date, court_name)
                        results.extend(court_results)
                        
                        logging.info(f"Found {len(court_results)} available slots for {court_name}")
                        
                    except Exception as e:
                        logging.error(f"Error checking court {i+1} for {academy_name}: {str(e)}")
                        continue
                
                # Add delay between dates
                if date != target_dates[-1]:  # Don't delay after last date
                    await asyncio.sleep(rate_limiting.get("delay_between_requests", 3))
            
            logging.info(f"Completed checking {academy_name}: {len(results)} total available slots found")
            
        except Exception as e:
            logging.error(f"Error checking academy {academy_name}: {str(e)}")
        
        return results
    
    async def _check_court_slots(self, page: Any, academy_name: str, date: str, court: str) -> List[Dict[str, Any]]:
        """
        Check time slots for a specific court
        """
        results = []
        
        try:
            # Wait for time slots to load
            await page.wait_for_selector(self.selectors["time_slots_container"], timeout=5000)
            
            # Get all time slot elements
            time_slot_elements = await page.query_selector_all(self.selectors["time_slots"])
            logging.info(f"Found {len(time_slot_elements)} time slots for {court}")
            
            for slot_element in time_slot_elements:
                try:
                    # Get slot time text
                    time_text = await slot_element.inner_text()
                    time_text = time_text.strip()
                    
                    if not time_text or ':' not in time_text:
                        continue
                    
                    # Get slot style to determine availability
                    style = await slot_element.get_attribute("style") or ""
                    
                    # Determine slot status based on style
                    # Available slots: style="" or no "color: red" and no "cursor: not-allowed"
                    # Unavailable slots: style="color: red; cursor: not-allowed;"
                    is_available = self._is_slot_available(style)
                    
                    if is_available:
                        result = {
                            "academy": academy_name,
                            "date": date,
                            "court": court,
                            "time": time_text,
                            "status": "available",
                            "booking_url": page.url,
                            "timestamp": datetime.now().isoformat()
                        }
                        results.append(result)
                        logging.info(f"✅ Available slot found: {academy_name} - {court} - {date} - {time_text}")
                    else:
                        logging.debug(f"❌ Slot unavailable: {academy_name} - {court} - {date} - {time_text}")
                    
                except Exception as e:
                    logging.error(f"Error processing time slot: {str(e)}")
                    continue
        
        except Exception as e:
            logging.error(f"Error checking court slots: {str(e)}")
        
        return results
    
    def _is_slot_available(self, style: str) -> bool:
        """
        Determine if a slot is available based on its style attribute
        Available slots have style="" or don't contain "color: red" and "cursor: not-allowed"
        Unavailable slots have style="color: red; cursor: not-allowed;"
        """
        if not style:
            return True  # Empty style means available
        
        # Check for unavailable indicators
        style_lower = style.lower()
        is_red = "color: red" in style_lower or "color:red" in style_lower
        is_not_allowed = "cursor: not-allowed" in style_lower or "cursor:not-allowed" in style_lower
        
        # Slot is unavailable if it has red color AND not-allowed cursor
        return not (is_red and is_not_allowed)
    
    async def get_all_available_slots(self, page: Any, academies: Dict[str, Dict], target_dates: List[str], rate_limiting: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Check all specified academies for available slots
        """
        all_results = []
        
        for academy_key, academy_info in academies.items():
            try:
                academy_results = await self.check_academy_slots(
                    page,
                    academy_info['url'],
                    academy_info['name'],
                    target_dates,
                    rate_limiting
                )
                all_results.extend(academy_results)
                
                # Add delay between academies
                if academy_key != list(academies.keys())[-1]:  # Don't delay after last academy
                    await asyncio.sleep(rate_limiting.get("delay_between_academies", 5))
                
            except Exception as e:
                logging.error(f"Error processing academy {academy_info['name']}: {str(e)}")
                continue
        
        return all_results
    
    def filter_slots_by_preferences(self, slots: List[Dict[str, Any]], time_preferences: Dict[str, Any], court_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter slots based on user preferences
        """
        filtered_slots = []
        
        for slot in slots:
            # Check time preferences
            if not self._matches_time_preference(slot["time"], time_preferences):
                continue
            
            # Check court preferences
            if not self._matches_court_preference(slot["court"], court_preferences):
                continue
            
            # Add preference level for prioritization
            slot["preference_level"] = self._get_preference_level(slot["time"], time_preferences)
            filtered_slots.append(slot)
        
        # Sort by preference level (preferred first)
        filtered_slots.sort(key=lambda x: 0 if x["preference_level"] == "preferred" else 1)
        
        return filtered_slots
    
    def _matches_time_preference(self, slot_time: str, time_preferences: Dict[str, Any]) -> bool:
        """Check if slot time matches preferences"""
        if time_preferences.get("notify_all", False):
            return True
        
        preferred_times = time_preferences.get("preferred", [])
        acceptable_times = time_preferences.get("acceptable", [])
        
        return slot_time in preferred_times or slot_time in acceptable_times
    
    def _matches_court_preference(self, court: str, court_preferences: Dict[str, Any]) -> bool:
        """Check if court matches preferences"""
        if court_preferences.get("check_all_courts", True):
            return True
        
        # Extract court number from "Court X" format
        try:
            court_number = int(court.split()[-1])
            preferred_courts = court_preferences.get("preferred_courts", [])
            return court_number in preferred_courts
        except (ValueError, IndexError):
            return True  # If we can't parse court number, include it
    
    def _get_preference_level(self, slot_time: str, time_preferences: Dict[str, Any]) -> str:
        """Get preference level for a time slot"""
        preferred_times = time_preferences.get("preferred", [])
        
        if slot_time in preferred_times:
            return "preferred"
        else:
            return "acceptable"
    
    def remove_duplicate_slots(self, slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate slots based on academy, date, court, and time"""
        seen = set()
        unique_slots = []
        
        for slot in slots:
            key = (slot["academy"], slot["date"], slot["court"], slot["time"])
            if key not in seen:
                seen.add(key)
                unique_slots.append(slot)
        
        return unique_slots
    
    def get_summary_stats(self, slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics of found slots"""
        if not slots:
            return {"total": 0, "by_academy": {}, "by_date": {}, "by_time": {}}
        
        stats = {
            "total": len(slots),
            "by_academy": {},
            "by_date": {},
            "by_time": {}
        }
        
        for slot in slots:
            # Count by academy
            academy = slot["academy"]
            stats["by_academy"][academy] = stats["by_academy"].get(academy, 0) + 1
            
            # Count by date
            date = slot["date"]
            stats["by_date"][date] = stats["by_date"].get(date, 0) + 1
            
            # Count by time
            time = slot["time"]
            stats["by_time"][time] = stats["by_time"].get(time, 0) + 1
        
        return stats
