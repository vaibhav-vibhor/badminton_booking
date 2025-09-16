"""
API-based booking checker using authentication tokens
Provides a more reliable alternative to browser automation
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import os

logger = logging.getLogger(__name__)

class BadmintonAPIChecker:
    """
    Token-based API client for badminton booking system
    Uses authentication tokens instead of browser automation
    """
    
    def __init__(self):
        self.base_url = "https://booking.gopichandacademy.com"
        self.api_base = "https://adminbooking.gopichandacademy.com/API"  # Updated to actual API base!
        self.session = requests.Session()
        self.login_token = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        # Token storage files
        self.token_file = "data/api_token.json"
        self.headers_file = "data/api_headers.json"
        
        # Setup default headers
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/'
        })
        
        # Academy mappings (from existing code)
        self.academies = {
            "Kotak Pullela Gopichand Badminton Academy": 1,
            "Pullela Gopichand Badminton Academy": 2, 
            "SAI Pullela Gopichand National Badminton Academy": 3
        }
    
    def load_existing_token(self) -> bool:
        """Load existing authentication token from session data"""
        try:
            # First try to load from API token file
            if os.path.exists(self.token_file):
                logger.info("🔍 Loading API token from file...")
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    
                # Check token age
                token_age = datetime.now() - datetime.fromisoformat(token_data['timestamp'])
                if token_age.total_seconds() < (7 * 24 * 3600):  # 7 days max
                    self.login_token = token_data['loginToken']
                    logger.info(f"✅ Loaded API token (age: {token_age.total_seconds()/3600:.1f} hours)")
                    return True
                else:
                    logger.info(f"⏰ API token too old ({token_age.total_seconds()/3600:.1f} hours)")
            
            # Fallback: try to load from browser session data
            session_file = "data/github_session.json"
            if os.path.exists(session_file):
                logger.info("🔍 Loading token from browser session data...")
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    
                # Check session age
                session_age = datetime.now() - datetime.fromisoformat(session_data['timestamp'])
                if session_age.total_seconds() < (7 * 24 * 3600):  # 7 days max
                    login_token = session_data.get('local_storage', {}).get('loginToken')
                    if login_token:
                        self.login_token = login_token
                        logger.info(f"✅ Loaded token from browser session (age: {session_age.total_seconds()/3600:.1f} hours)")
                        # Save to API token file for future use
                        self.save_token()
                        return True
                    else:
                        logger.warning("❌ No loginToken found in browser session")
                else:
                    logger.info(f"⏰ Browser session too old ({session_age.total_seconds()/3600:.1f} hours)")
            
            logger.info("❌ No valid tokens found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error loading token: {e}")
            return False
    
    def save_token(self):
        """Save current authentication token"""
        try:
            if not self.login_token:
                return
                
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            
            token_data = {
                'loginToken': self.login_token,
                'timestamp': datetime.now().isoformat(),
                'user_agent': self.user_agent
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            logger.info("💾 API token saved successfully")
            
        except Exception as e:
            logger.error(f"❌ Error saving token: {e}")
    
    def set_auth_headers(self):
        """Set authentication headers for requests"""
        if self.login_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.login_token}',
                'X-Login-Token': self.login_token
            })
            logger.info("🔐 Authentication headers set")
    
    async def verify_token(self) -> bool:
        """
        Verify if the current login token is still valid using the Profile API
        
        Returns:
            True if token is valid, False otherwise
        """
        if not self.login_token:
            logger.info("❌ No token to verify")
            return False
            
        try:
            # Use the REAL profile endpoint to verify token
            endpoint = f"{self.api_base}/Customer/Data/Get/Profile"
            
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'LoginToken': self.login_token,  # This is the key authentication method!
                'Origin': 'https://booking.gopichandacademy.com',
                'Referer': 'https://booking.gopichandacademy.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Sec-GPC': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            logger.info("🔐 Verifying login token using Profile API...")
            
            response = self.session.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('Status') == 'Success':
                        user_info = data.get('Result', {})
                        user_name = user_info.get('name', 'Unknown')
                        user_mobile = user_info.get('mobile', 'Unknown')
                        logger.info(f"✅ Token valid! User: {user_name} ({user_mobile})")
                        return True
                    else:
                        logger.warning(f"❌ Token verification failed: {data.get('Message')}")
                        return False
                except json.JSONDecodeError:
                    logger.error("❌ Invalid JSON response from profile API")
                    return False
            elif response.status_code == 401:
                logger.warning("❌ Token expired or invalid (401)")
                return False
            else:
                logger.warning(f"❌ Profile API returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error verifying token: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error verifying token: {e}")
            return False
                
            self.set_auth_headers()
            
            # Try multiple endpoints to find the correct API structure
            logger.info("🔍 Verifying token validity...")
            
            test_endpoints = [
                # Try different possible API structures
                f"{self.base_url}/api/user/profile",
                f"{self.base_url}/api/auth/verify",
                f"{self.base_url}/API/user/profile", 
                f"{self.base_url}/API/auth/verify",
                f"{self.base_url}/api/venues",
                f"{self.base_url}/API/venues",
                # Try with venue-details (the working browser endpoint)
                f"{self.base_url}/venue-details/1",
                # Try without API prefix
                f"{self.base_url}/auth/verify",
                f"{self.base_url}/user/profile",
            ]
            
            for i, endpoint in enumerate(test_endpoints):
                try:
                    logger.debug(f"� Testing endpoint {i+1}/{len(test_endpoints)}: {endpoint}")
                    
                    response = self.session.get(endpoint, timeout=10)
                    logger.debug(f"📊 Response: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Token verified with endpoint: {endpoint}")
                        # Update our API base to the working pattern
                        if "/API/" in endpoint:
                            self.api_base = f"{self.base_url}/API"
                        elif "/api/" in endpoint:
                            self.api_base = f"{self.base_url}/api"
                        else:
                            self.api_base = self.base_url
                        
                        logger.info(f"🔧 Updated API base to: {self.api_base}")
                        return True
                        
                    elif response.status_code == 401:
                        logger.info("❌ Token expired or invalid (401 response)")
                        return False
                        
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Network error on {endpoint}: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Error testing {endpoint}: {e}")
                    continue
            
            # If all endpoints failed, try a different approach - check if we can access the main page
            logger.info("🔍 Trying to verify token by accessing main booking page...")
            
            try:
                response = self.session.get(f"{self.base_url}/", timeout=10)
                
                if response.status_code == 200:
                    # Check if the response contains logged-in indicators
                    content = response.text.lower()
                    
                    # Look for signs that we're logged in
                    logged_in_indicators = [
                        'logout', 'profile', 'dashboard', 'booking', 'user',
                        'login-token', 'logintoken'
                    ]
                    
                    indicators_found = sum(1 for indicator in logged_in_indicators if indicator in content)
                    
                    if indicators_found >= 2:
                        logger.info(f"✅ Token appears valid based on main page content ({indicators_found} indicators)")
                        return True
                    else:
                        logger.info(f"❌ Token verification inconclusive ({indicators_found} indicators)")
                        
            except Exception as e:
                logger.debug(f"Error testing main page: {e}")
            
            logger.info("❌ Token verification failed on all endpoints")
            return False
                
        except Exception as e:
            logger.error(f"❌ Token verification failed: {e}")
            return False
    
    async def get_venue_slots(self, venue_id: int, date: str) -> Optional[List[Dict]]:
        """
        Get available slots for a venue on a specific date using the real API endpoint
        
        Args:
            venue_id: Academy venue ID (1, 2, or 3)
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of slot dictionaries or None if failed
        """
        try:
            if not self.login_token:
                logger.warning("⚠️ No authentication token - trying without auth...")
                
            # Use the ACTUAL API endpoint discovered from curl
            endpoint = f"{self.api_base}/Get/Calender"
            params = {
                'venue_id': venue_id,
                'date': date
            }
            
            # Set up headers similar to the curl request
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Origin': 'https://booking.gopichandacademy.com',
                'Referer': 'https://booking.gopichandacademy.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Sec-GPC': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            logger.info(f"📡 Fetching slots for venue {venue_id} on {date} using REAL API...")
            logger.debug(f"🔗 URL: {endpoint}?venue_id={venue_id}&date={date}")
            
            response = self.session.get(endpoint, params=params, headers=headers, timeout=15)
            
            logger.debug(f"📊 Response: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"✅ Got API response: {len(str(data))} characters")
                    
                    # Parse the REAL response format
                    slots = self.parse_calendar_api_response(data, date)
                    if slots:
                        logger.info(f"🎯 Successfully parsed {len(slots)} courts with slots!")
                        return slots
                    else:
                        logger.warning("⚠️ No slots found in API response")
                        return []
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    logger.debug(f"Response text: {response.text[:500]}")
                    return None
                    
            elif response.status_code == 401:
                logger.warning("❌ Authentication failed - token may be expired")
                return None
            else:
                logger.warning(f"❌ API call failed with status {response.status_code}")
                logger.debug(f"Response: {response.text[:200]}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching venue slots: {e}")
            return None
    
    def parse_calendar_api_response(self, data: dict, date: str) -> List[Dict]:
        """
        Parse the actual calendar API response format
        
        Expected format:
        {
            "Status": "Success",
            "Message": "Data found successfully.",
            "Result": {
                "1": {
                    "court_name": "1",
                    "court_available_slots": ["12:00-13:00|1|405", ...]
                }
            }
        }
        """
        try:
            if data.get('Status') != 'Success':
                logger.warning(f"❌ API returned error: {data.get('Message', 'Unknown error')}")
                return []
                
            result = data.get('Result', {})
            if not result:
                logger.info("ℹ️ No court data in API response")
                return []
                
            slots = []
            
            for court_id, court_data in result.items():
                court_name = court_data.get('court_name', f'Court {court_id}')
                court_type = court_data.get('court_type', 'Unknown')
                court_charges = court_data.get('court_charges', '0')
                available_slots = court_data.get('court_available_slots', [])
                
                # Parse available slots - format: "12:00-13:00|1|405"
                # Where: time_slot|availability(1=available,0=booked)|price
                available_times = []
                all_time_slots = {}  # Store all slots with their availability status
                total_available = 0
                
                for slot_str in available_slots:
                    try:
                        parts = slot_str.split('|')
                        if len(parts) >= 3:
                            time_slot = parts[0]
                            is_available = parts[1] == '1'
                            price = parts[2]
                            
                            # Store all time slots with their status
                            all_time_slots[time_slot] = {
                                'available': is_available,
                                'price': price
                            }
                            
                            if is_available:
                                available_times.append(time_slot)
                                total_available += 1
                                
                    except Exception as e:
                        logger.debug(f"Error parsing slot '{slot_str}': {e}")
                        continue
                
                # Create slot entry
                slot_entry = {
                    'court_id': court_id,
                    'court_name': court_name,
                    'court_type': court_type,
                    'court_charges': court_charges,
                    'date': date,
                    'available': total_available > 0,
                    'available_slots': total_available,
                    'time_slots': available_times,  # For backward compatibility
                    'all_time_slots': all_time_slots  # New: all slots with status
                }
                
                slots.append(slot_entry)
                logger.debug(f"📊 Court {court_name}: {total_available} slots available")
            
            logger.info(f"✅ Parsed {len(slots)} courts with total available slots")
            return slots
            
        except Exception as e:
            logger.error(f"❌ Error parsing calendar API response: {e}")
            return []
    
    def parse_html_response(self, html: str, venue_id: int, date: str) -> List[Dict]:
        """
        Parse slot information from HTML response
        Useful when API returns HTML instead of JSON
        """
        try:
            slots = []
            
            # Simple HTML parsing to extract court/slot information
            # This is a basic implementation - could be enhanced with BeautifulSoup
            
            import re
            
            # Look for patterns that might indicate court information
            court_patterns = [
                r'court["\s]*:[\s]*["\']([^"\']+)["\']',
                r'court["\s]*["\']([^"\']+)["\']',
                r'name["\s]*:[\s]*["\']([^"\']+)["\'].*court',
            ]
            
            # Look for availability patterns
            availability_patterns = [
                r'available["\s]*:[\s]*(\d+)',
                r'slots["\s]*:[\s]*(\d+)',
                r'free["\s]*:[\s]*(\d+)',
            ]
            
            courts_found = []
            for pattern in court_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                courts_found.extend(matches)
            
            availability_found = []
            for pattern in availability_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                availability_found.extend([int(m) for m in matches if m.isdigit()])
            
            # Try to match courts with availability
            for i, court in enumerate(courts_found[:len(availability_found)]):
                if i < len(availability_found):
                    slots.append({
                        'date': date,
                        'venue_id': venue_id,
                        'court_name': court,
                        'available_slots': availability_found[i],
                        'available': availability_found[i] > 0,
                        'source': 'html_parsing'
                    })
            
            if slots:
                logger.info(f"✅ Parsed {len(slots)} slots from HTML response")
            else:
                logger.debug("❌ Could not parse any slots from HTML response")
                
            return slots
            
        except Exception as e:
            logger.error(f"❌ Error parsing HTML response: {e}")
            return []
    
    def parse_slots_from_api_response(self, data: Dict, date: str) -> List[Dict]:
        """
        Parse slot information from API response
        
        Args:
            data: Raw API response data
            date: Date string for context
            
        Returns:
            List of parsed slot dictionaries
        """
        try:
            slots = []
            
            # The structure may vary, let's try different possible structures
            logger.debug(f"📋 Parsing API response structure...")
            
            # Log the keys to understand structure
            if isinstance(data, dict):
                logger.debug(f"📋 Response keys: {list(data.keys())[:10]}")  # First 10 keys
                
                # Look for common slot data structures
                possible_slot_keys = ['slots', 'courts', 'bookings', 'availability', 'data', 'results']
                
                for key in possible_slot_keys:
                    if key in data:
                        logger.info(f"✅ Found potential slot data in '{key}' field")
                        slot_data = data[key]
                        
                        if isinstance(slot_data, list):
                            for item in slot_data:
                                if isinstance(item, dict):
                                    # Extract slot information
                                    slot_info = self.extract_slot_info(item, date)
                                    if slot_info:
                                        slots.append(slot_info)
                        elif isinstance(slot_data, dict):
                            # Single court/venue data
                            slot_info = self.extract_slot_info(slot_data, date)
                            if slot_info:
                                slots.append(slot_info)
                
                # If no specific keys found, try to parse the whole response
                if not slots and data:
                    logger.info("🔍 Attempting to parse entire response structure...")
                    slot_info = self.extract_slot_info(data, date)
                    if slot_info:
                        slots.append(slot_info)
            
            logger.info(f"📊 Parsed {len(slots)} slot entries")
            return slots
            
        except Exception as e:
            logger.error(f"❌ Error parsing slots from API response: {e}")
            return []
    
    def extract_slot_info(self, item: Dict, date: str) -> Optional[Dict]:
        """Extract relevant slot information from a single item"""
        try:
            slot_info = {
                'date': date,
                'available': False,
                'total_slots': 0,
                'available_slots': 0,
                'court_name': 'Unknown',
                'raw_data': item  # Keep raw data for debugging
            }
            
            # Try to extract court/slot information
            # Common field names to look for
            name_fields = ['name', 'court_name', 'title', 'court', 'venue']
            for field in name_fields:
                if field in item:
                    slot_info['court_name'] = str(item[field])
                    break
            
            # Look for availability information
            availability_fields = ['available', 'availability', 'slots_available', 'free_slots']
            for field in availability_fields:
                if field in item:
                    slot_info['available_slots'] = int(item[field]) if item[field] else 0
                    slot_info['available'] = slot_info['available_slots'] > 0
                    break
            
            # Look for total slots
            total_fields = ['total', 'total_slots', 'capacity', 'max_slots']
            for field in total_fields:
                if field in item:
                    slot_info['total_slots'] = int(item[field]) if item[field] else 0
                    break
            
            return slot_info
            
        except Exception as e:
            logger.debug(f"Error extracting slot info: {e}")
            return None
    
    async def check_all_academies(self, dates: List[str]) -> Dict[str, List[Dict]]:
        """
        Check all academies for available slots on given dates
        
        Args:
            dates: List of date strings in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping academy names to their slot data
        """
        results = {}
        
        # Try to verify token if we have one (for authenticated APIs later)
        if self.login_token:
            logger.info("� Verifying authentication token...")
            if await self.verify_token():
                logger.info("✅ Token verified - can use authenticated APIs")
            else:
                logger.warning("⚠️ Token verification failed - using public APIs only")
        else:
            logger.info("🔓 No token available - using public Calendar API")
        
        logger.info(f"🏸 Checking {len(self.academies)} academies for {len(dates)} dates using API...")
        
        for academy_name, venue_id in self.academies.items():
            logger.info(f"🏸 Checking: {academy_name} (ID: {venue_id})")
            academy_slots = []
            
            for date in dates:
                logger.info(f"   📅 Checking {date}")
                slots = await self.get_venue_slots(venue_id, date)
                
                if slots:
                    academy_slots.extend(slots)
                    available_count = sum(1 for slot in slots if slot['available'])
                    logger.info(f"      ✅ Found {available_count} available slots")
                else:
                    logger.info(f"      ❌ No data received for {date}")
                
                # Small delay between requests to be respectful
                await asyncio.sleep(1)
            
            results[academy_name] = academy_slots
            total_available = sum(1 for slot in academy_slots if slot['available'])
            logger.info(f"✅ {academy_name}: {total_available} total available slots")
        
        return results
    
    def format_results_for_telegram(self, results: Dict[str, List[Dict]]) -> str:
        """
        Format API results for Telegram message with detailed table format
        Shows courts as rows and time slots as columns with ✓/✗ symbols
        """
        try:
            if not results or not any(results.values()):
                return "❌ No slots found via API"

            message_lines = ["🏸 *Badminton Slots Available* (API)"]
            total_available_slots = 0
            
            for academy_name, slots in results.items():
                if not slots:
                    continue
                    
                # Create academy header
                short_name = academy_name.replace("Pullela Gopichand Badminton Academy", "Pullela").replace("SAI ", "")
                message_lines.append(f"\n📍 *{short_name}*")
                
                # Group by date
                dates_data = {}
                for slot in slots:
                    date = slot['date']
                    if date not in dates_data:
                        dates_data[date] = []
                    dates_data[date].append(slot)
                
                for date, date_slots in dates_data.items():
                    # Format date
                    try:
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%a %b %d')
                    except:
                        formatted_date = date
                    
                    message_lines.append(f"  📅 {formatted_date}")
                    
                    # Check if there are any available slots for this date
                    date_has_available_slots = any(slot.get('available', False) for slot in date_slots)
                    
                    if not date_has_available_slots:
                        message_lines.append(f"    ❌ No slots available")
                        continue
                    
                    # Collect all time slots from all courts for this date
                    all_time_slots_set = set()
                    for slot in date_slots:
                        if 'all_time_slots' in slot:
                            all_time_slots_set.update(slot['all_time_slots'].keys())
                    
                    if not all_time_slots_set:
                        # Fallback to old format if no detailed data
                        for slot in date_slots:
                            court_name = slot['court_name']
                            available = slot['available_slots']
                            if available > 0:
                                message_lines.append(f"    ✅ {court_name}: {available} slots")
                        continue
                    
                    # Sort time slots (convert to 24h format for sorting)
                    def time_sort_key(time_slot):
                        try:
                            # Extract start time from "12:00-13:00" format
                            start_time = time_slot.split('-')[0]
                            hour, minute = start_time.split(':')
                            return int(hour) * 100 + int(minute)
                        except:
                            return 9999
                    
                    sorted_time_slots = sorted(all_time_slots_set, key=time_sort_key)
                    
                    # Create table header with time slots
                    # Use 24h format for display
                    def format_time_for_header(time_slot):
                        try:
                            start_time = time_slot.split('-')[0]
                            hour = int(start_time.split(':')[0])
                            return f"{hour:02d}h"
                        except:
                            return time_slot[:2]
                    
                    time_headers = [format_time_for_header(slot) for slot in sorted_time_slots]
                    
                    # Limit to reasonable number of columns (Telegram width limit)
                    max_columns = 8
                    if len(time_headers) > max_columns:
                        time_headers = time_headers[:max_columns]
                        sorted_time_slots = sorted_time_slots[:max_columns]
                    
                    # Create header row with precise spacing for emoji alignment  
                    header = "```\n"
                    header += "   " + "".join(f"{h:>6}" for h in time_headers) + "\n"
                    message_lines.append(header)
                    
                    # Create rows for each court
                    court_rows = []
                    date_available_count = 0
                    
                    for slot in date_slots:
                        court_name = slot['court_name']
                        all_slots = slot.get('all_time_slots', {})
                        
                        row = f"{court_name:>2} "
                        for time_slot in sorted_time_slots:
                            if time_slot in all_slots:
                                is_available = all_slots[time_slot]['available']
                                symbol = "✅" if is_available else "❌"
                                if is_available:
                                    date_available_count += 1
                            else:
                                symbol = "-"
                            # Center emoji in fixed 6-character column
                            row += f"{symbol:^6}"
                        
                        court_rows.append(row)
                    
                    # Add court rows
                    for row in court_rows:
                        message_lines.append(row)
                    
                    message_lines.append("```")
                    
                    total_available_slots += date_available_count
                    if date_available_count > 0:
                        message_lines.append(f"    📊 {date_available_count} slots available")
            
            # Add total
            if total_available_slots > 0:
                message_lines.append(f"\n🎯 *Total: {total_available_slots} slots*")
            else:
                message_lines.append(f"\n❌ *No slots currently available*")
                
            message_lines.append(f"⚡ *Via API* - {datetime.now().strftime('%H:%M')}")
            
            return "\n".join(message_lines)
            
        except Exception as e:
            logger.error(f"❌ Error formatting results for Telegram: {e}")
            return f"❌ Error formatting results: {str(e)}"


class HybridBookingChecker:
    """
    Hybrid checker that tries API first, falls back to browser automation
    """
    
    def __init__(self, browser_checker):
        self.api_checker = BadmintonAPIChecker()
        self.browser_checker = browser_checker
        self.prefer_api = True
    
    async def check_slots(self, dates: List[str]) -> Tuple[str, bool]:
        """
        Check slots using API first, fallback to browser if needed
        
        Returns:
            Tuple of (message, used_api)
        """
        # Try API approach first
        if self.prefer_api:
            logger.info("🚀 Attempting API-based slot checking...")
            
            # Load existing token
            if self.api_checker.load_existing_token():
                # Verify token and get results
                try:
                    results = await self.api_checker.check_all_academies(dates)
                    
                    if results and any(results.values()):
                        message = self.api_checker.format_results_for_telegram(results)
                        logger.info("✅ API approach successful!")
                        return message, True
                    else:
                        logger.warning("⚠️ API returned no results - falling back to browser")
                except Exception as e:
                    logger.error(f"❌ API approach failed: {e}")
            else:
                logger.info("❌ No valid API token found - falling back to browser")
        
        # Fallback to browser automation
        logger.info("🌐 Falling back to browser automation...")
        try:
            # Run the existing browser automation
            browser_results = await self.browser_checker.run_check(dates)
            return browser_results, False
            
        except Exception as e:
            logger.error(f"❌ Browser automation also failed: {e}")
            return f"❌ Both API and browser approaches failed: {str(e)}", False
