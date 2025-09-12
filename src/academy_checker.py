import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

class AcademyChecker:
    """
    Coordinates checking across multiple academies and manages academy-specific logic
    """
    
    def __init__(self):
        # Academy configuration with detailed information
        self.academies = {
            "kotak": {
                "name": "Kotak Pullela Gopichand Badminton Academy",
                "url": "https://booking.gopichandacademy.com/venue-details/1",
                "id": 1,
                "short_name": "Kotak",
                "location": "Location 1",
                "typical_courts": 9  # Based on the HTML showing courts 1-9
            },
            "pullela": {
                "name": "Pullela Gopichand Badminton Academy", 
                "url": "https://booking.gopichandacademy.com/venue-details/2",
                "id": 2,
                "short_name": "Pullela",
                "location": "Location 2",
                "typical_courts": 9
            },
            "sai": {
                "name": "SAI Gopichand Pullela Gopichand Badminton Academy",
                "url": "https://booking.gopichandacademy.com/venue-details/3", 
                "id": 3,
                "short_name": "SAI Gopichand",
                "location": "Location 3",
                "typical_courts": 9
            }
        }
    
    def get_academies_to_check(self, academy_preferences: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get filtered list of academies based on preferences
        """
        if not academy_preferences or "all" in academy_preferences:
            return self.academies
        
        filtered_academies = {}
        for academy_key in academy_preferences:
            if academy_key in self.academies:
                filtered_academies[academy_key] = self.academies[academy_key]
            else:
                logging.warning(f"Unknown academy preference: {academy_key}")
        
        return filtered_academies
    
    def get_academy_info(self, academy_key: str) -> Dict[str, Any]:
        """Get information about a specific academy"""
        return self.academies.get(academy_key, {})
    
    def get_all_academy_names(self) -> List[str]:
        """Get list of all academy names"""
        return [info["name"] for info in self.academies.values()]
    
    def get_academy_by_url(self, url: str) -> Dict[str, Any]:
        """Find academy by its URL"""
        for academy_info in self.academies.values():
            if academy_info["url"] == url:
                return academy_info
        return {}
    
    def validate_academy_access(self, results: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Validate which academies are accessible based on results
        Returns a dict mapping academy names to accessibility status
        """
        academy_access = {}
        
        # Initialize all academies as not accessible
        for academy_info in self.academies.values():
            academy_access[academy_info["name"]] = False
        
        # Mark academies as accessible if we got results from them
        for result in results:
            academy_name = result.get("academy")
            if academy_name:
                academy_access[academy_name] = True
        
        return academy_access
    
    def generate_academy_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive report of slot availability by academy
        """
        if not results:
            return "No available slots found across all academies."
        
        # Group results by academy
        academy_results = {}
        for result in results:
            academy = result["academy"]
            if academy not in academy_results:
                academy_results[academy] = []
            academy_results[academy].append(result)
        
        report_lines = [f"📊 Badminton Slot Availability Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        report_lines.append("=" * 60)
        
        # Summary
        total_slots = len(results)
        total_academies = len(academy_results)
        report_lines.append(f"🏸 Total Available Slots: {total_slots}")
        report_lines.append(f"🏢 Academies with slots: {total_academies}")
        report_lines.append("")
        
        # Detailed breakdown by academy
        for academy_name, academy_slots in academy_results.items():
            academy_info = self.get_academy_by_name(academy_name)
            short_name = academy_info.get("short_name", academy_name)
            
            report_lines.append(f"🏛️ {short_name}")
            report_lines.append(f"   Available slots: {len(academy_slots)}")
            
            # Group by date
            date_groups = {}
            for slot in academy_slots:
                date = slot["date"]
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(slot)
            
            for date in sorted(date_groups.keys()):
                report_lines.append(f"   📅 {date}:")
                date_slots = date_groups[date]
                
                # Group by court
                court_groups = {}
                for slot in date_slots:
                    court = slot["court"]
                    if court not in court_groups:
                        court_groups[court] = []
                    court_groups[court].append(slot["time"])
                
                for court in sorted(court_groups.keys()):
                    times = sorted(court_groups[court])
                    times_str = ", ".join(times)
                    report_lines.append(f"      🏟️ {court}: {times_str}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def get_academy_by_name(self, academy_name: str) -> Dict[str, Any]:
        """Find academy information by name"""
        for academy_info in self.academies.values():
            if academy_info["name"] == academy_name:
                return academy_info
        return {}
    
    def get_priority_slots(self, results: List[Dict[str, Any]], max_priority_slots: int = 5) -> List[Dict[str, Any]]:
        """
        Get priority slots based on various factors:
        - Preference level (preferred times first)
        - Earlier dates
        - Earlier times
        """
        if not results:
            return []
        
        # Sort by multiple criteria
        def sort_key(slot):
            # Preference level (0 = preferred, 1 = acceptable)
            pref_order = 0 if slot.get("preference_level") == "preferred" else 1
            
            # Date (earlier dates first)
            date_str = slot.get("date", "9999-12-31")
            
            # Time (earlier times first) - convert "HH:MM-HH:MM" to just start time
            time_str = slot.get("time", "23:59-23:59")
            start_time = time_str.split("-")[0] if "-" in time_str else time_str
            
            return (pref_order, date_str, start_time)
        
        sorted_results = sorted(results, key=sort_key)
        return sorted_results[:max_priority_slots]
    
    def get_academy_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed statistics about slot availability"""
        if not results:
            return {
                "total_slots": 0,
                "academies_checked": list(self.academies.keys()),
                "academies_with_slots": [],
                "date_range": None,
                "time_distribution": {},
                "court_utilization": {}
            }
        
        # Basic stats
        total_slots = len(results)
        academies_with_slots = list(set(result["academy"] for result in results))
        
        # Date range
        dates = [result["date"] for result in results]
        date_range = {"start": min(dates), "end": max(dates)} if dates else None
        
        # Time distribution
        time_distribution = {}
        for result in results:
            time = result["time"]
            time_distribution[time] = time_distribution.get(time, 0) + 1
        
        # Court utilization by academy
        court_utilization = {}
        for result in results:
            academy = result["academy"]
            court = result["court"]
            
            if academy not in court_utilization:
                court_utilization[academy] = {}
            
            court_utilization[academy][court] = court_utilization[academy].get(court, 0) + 1
        
        return {
            "total_slots": total_slots,
            "academies_checked": list(self.academies.keys()),
            "academies_with_slots": academies_with_slots,
            "date_range": date_range,
            "time_distribution": time_distribution,
            "court_utilization": court_utilization
        }
    
    def format_slot_for_notification(self, slot: Dict[str, Any]) -> str:
        """Format a single slot for notification"""
        academy_info = self.get_academy_by_name(slot["academy"])
        short_name = academy_info.get("short_name", slot["academy"])
        
        # Format date nicely
        try:
            date_obj = datetime.strptime(slot["date"], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %b %Y (%A)")
        except:
            formatted_date = slot["date"]
        
        return (
            f"🏸 {short_name}\n"
            f"📅 {formatted_date}\n"
            f"🏟️ {slot['court']}\n"
            f"⏰ {slot['time']}\n"
            f"🔗 {slot['booking_url']}"
        )
    
    def check_date_validity(self, dates: List[str]) -> List[str]:
        """
        Check which dates are valid and not in the past
        Returns list of valid dates
        """
        today = datetime.now().date()
        valid_dates = []
        
        for date_str in dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj >= today:
                    valid_dates.append(date_str)
                else:
                    logging.warning(f"Skipping past date: {date_str}")
            except ValueError:
                logging.error(f"Invalid date format: {date_str}")
                continue
        
        return valid_dates
