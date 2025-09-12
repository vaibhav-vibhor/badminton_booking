import logging
import json
import os
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Tuple, Optional

class SlotAnalyzer:
    """
    Utility class for analyzing and processing badminton slot data
    """
    
    @staticmethod
    def parse_time_slot(time_text: str) -> Dict[str, Any]:
        """
        Parse time slot text like "18:00-19:00" into structured data
        """
        try:
            if '-' not in time_text:
                return {"valid": False, "error": "Invalid time format"}
            
            start_time, end_time = time_text.split('-')
            start_time = start_time.strip()
            end_time = end_time.strip()
            
            # Parse times
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour, end_min = map(int, end_time.split(':'))
            
            # Calculate duration
            start_datetime = datetime.combine(datetime.today(), time(start_hour, start_min))
            end_datetime = datetime.combine(datetime.today(), time(end_hour, end_min))
            duration = end_datetime - start_datetime
            
            return {
                "valid": True,
                "start": start_time,
                "end": end_time,
                "start_hour": start_hour,
                "end_hour": end_hour,
                "duration_minutes": duration.total_seconds() / 60,
                "is_peak_hours": SlotAnalyzer.is_peak_hours(start_hour),
                "time_of_day": SlotAnalyzer.categorize_time_of_day(start_hour)
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    @staticmethod
    def is_peak_hours(hour: int) -> bool:
        """Check if the hour is during peak playing hours"""
        # Peak hours are typically 6 PM to 10 PM (18:00 to 22:00)
        return 18 <= hour < 22
    
    @staticmethod
    def categorize_time_of_day(hour: int) -> str:
        """Categorize time slot by time of day"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    @staticmethod
    def filter_by_time_preferences(slots: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter slots based on time preferences with detailed matching
        """
        if not slots or not preferences:
            return slots
        
        if preferences.get("notify_all", False):
            return slots
        
        preferred_times = set(preferences.get("preferred", []))
        acceptable_times = set(preferences.get("acceptable", []))
        
        filtered_slots = []
        
        for slot in slots:
            slot_time = slot.get("time", "")
            
            if slot_time in preferred_times:
                slot["preference_level"] = "preferred"
                slot["preference_score"] = 3
                filtered_slots.append(slot)
            elif slot_time in acceptable_times:
                slot["preference_level"] = "acceptable"
                slot["preference_score"] = 2
                filtered_slots.append(slot)
            elif preferences.get("include_nearby_times", False):
                # Check for nearby time slots (within 1 hour)
                if SlotAnalyzer._is_nearby_time(slot_time, preferred_times | acceptable_times):
                    slot["preference_level"] = "nearby"
                    slot["preference_score"] = 1
                    filtered_slots.append(slot)
        
        # Sort by preference score (highest first)
        filtered_slots.sort(key=lambda x: x.get("preference_score", 0), reverse=True)
        
        return filtered_slots
    
    @staticmethod
    def _is_nearby_time(slot_time: str, target_times: set, tolerance_minutes: int = 60) -> bool:
        """Check if slot time is near any target times"""
        try:
            slot_parsed = SlotAnalyzer.parse_time_slot(slot_time)
            if not slot_parsed["valid"]:
                return False
            
            slot_start = slot_parsed["start_hour"] * 60 + int(slot_parsed["start"].split(':')[1])
            
            for target_time in target_times:
                target_parsed = SlotAnalyzer.parse_time_slot(target_time)
                if not target_parsed["valid"]:
                    continue
                
                target_start = target_parsed["start_hour"] * 60 + int(target_parsed["start"].split(':')[1])
                
                if abs(slot_start - target_start) <= tolerance_minutes:
                    return True
            
            return False
        except:
            return False
    
    @staticmethod
    def filter_by_court_preferences(slots: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter slots based on court preferences"""
        if not slots or not preferences:
            return slots
        
        if preferences.get("check_all_courts", True):
            return slots
        
        preferred_courts = set(preferences.get("preferred_courts", []))
        
        filtered_slots = []
        for slot in slots:
            court_str = slot.get("court", "")
            
            # Extract court number from "Court X" format
            try:
                court_number = int(court_str.split()[-1])
                if court_number in preferred_courts:
                    filtered_slots.append(slot)
            except (ValueError, IndexError):
                # If we can't parse court number, include it (better safe than sorry)
                filtered_slots.append(slot)
        
        return filtered_slots
    
    @staticmethod
    def remove_duplicate_slots(slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate slots while preserving the best preference level"""
        if not slots:
            return slots
        
        # Create a dictionary to track unique slots
        unique_slots = {}
        
        for slot in slots:
            key = (slot["academy"], slot["date"], slot["court"], slot["time"])
            
            if key not in unique_slots:
                unique_slots[key] = slot
            else:
                # Keep the slot with better preference level
                existing_score = unique_slots[key].get("preference_score", 0)
                current_score = slot.get("preference_score", 0)
                
                if current_score > existing_score:
                    unique_slots[key] = slot
        
        return list(unique_slots.values())
    
    @staticmethod
    def group_slots_by_criteria(slots: List[Dict[str, Any]], group_by: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group slots by various criteria"""
        grouped = {}
        
        for slot in slots:
            if group_by == "academy":
                key = slot.get("academy", "Unknown")
            elif group_by == "date":
                key = slot.get("date", "Unknown")
            elif group_by == "time":
                key = slot.get("time", "Unknown")
            elif group_by == "court":
                key = slot.get("court", "Unknown")
            elif group_by == "preference_level":
                key = slot.get("preference_level", "none")
            else:
                key = "all"
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(slot)
        
        return grouped
    
    @staticmethod
    def generate_availability_report(slots: List[Dict[str, Any]]) -> str:
        """Generate a detailed availability report"""
        if not slots:
            return "No slots available."
        
        # Basic statistics
        total_slots = len(slots)
        unique_dates = len(set(slot["date"] for slot in slots))
        unique_academies = len(set(slot["academy"] for slot in slots))
        
        # Time analysis
        time_distribution = SlotAnalyzer.group_slots_by_criteria(slots, "time")
        popular_times = sorted(time_distribution.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        
        # Academy analysis
        academy_distribution = SlotAnalyzer.group_slots_by_criteria(slots, "academy")
        
        # Preference analysis
        preference_distribution = SlotAnalyzer.group_slots_by_criteria(slots, "preference_level")
        
        report = [
            "📊 BADMINTON SLOT AVAILABILITY REPORT",
            "=" * 50,
            f"📈 Total Available Slots: {total_slots}",
            f"📅 Dates Covered: {unique_dates}",
            f"🏢 Academies with Slots: {unique_academies}",
            "",
            "🕐 Most Popular Times:"
        ]
        
        for time_slot, time_slots in popular_times:
            report.append(f"   {time_slot}: {len(time_slots)} slots")
        
        report.extend([
            "",
            "🏛️ Availability by Academy:"
        ])
        
        for academy, academy_slots in academy_distribution.items():
            short_name = academy.split()[0] if academy else "Unknown"
            report.append(f"   {short_name}: {len(academy_slots)} slots")
        
        if preference_distribution:
            report.extend([
                "",
                "⭐ Preference Distribution:"
            ])
            for level, level_slots in preference_distribution.items():
                report.append(f"   {level.title()}: {len(level_slots)} slots")
        
        return "\n".join(report)


class DateTimeUtils:
    """
    Utility class for date and time operations
    """
    
    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """Check if date string is valid and not in the past"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            return date_obj >= datetime.now().date()
        except ValueError:
            return False
    
    @staticmethod
    def get_next_n_days(n: int, include_today: bool = True) -> List[str]:
        """Get list of next N days in YYYY-MM-DD format"""
        start_date = datetime.now().date()
        if not include_today:
            start_date += timedelta(days=1)
        
        return [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]
    
    @staticmethod
    def get_weekdays_only(dates: List[str]) -> List[str]:
        """Filter dates to include only weekdays"""
        weekdays = []
        for date_str in dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj.weekday() < 5:  # Monday = 0, Friday = 4
                    weekdays.append(date_str)
            except ValueError:
                continue
        return weekdays
    
    @staticmethod
    def get_weekends_only(dates: List[str]) -> List[str]:
        """Filter dates to include only weekends"""
        weekends = []
        for date_str in dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    weekends.append(date_str)
            except ValueError:
                continue
        return weekends
    
    @staticmethod
    def format_date_for_display(date_str: str) -> str:
        """Format date for user-friendly display"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            return date_obj.strftime("%d %b %Y (%A)")
        except ValueError:
            return date_str
    
    @staticmethod
    def time_until_slot(date_str: str, time_str: str) -> str:
        """Calculate time remaining until a slot"""
        try:
            # Parse the date and time
            date_part = datetime.strptime(date_str, "%Y-%m-%d").date()
            time_part = datetime.strptime(time_str.split('-')[0], "%H:%M").time()
            
            # Combine date and time
            slot_datetime = datetime.combine(date_part, time_part)
            now = datetime.now()
            
            if slot_datetime <= now:
                return "Past"
            
            delta = slot_datetime - now
            
            if delta.days > 0:
                return f"{delta.days} days"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hours"
            else:
                minutes = delta.seconds // 60
                return f"{minutes} minutes"
                
        except Exception:
            return "Unknown"


class DataPersistence:
    """
    Utility class for data persistence and caching
    """
    
    @staticmethod
    def save_slots_to_file(slots: List[Dict[str, Any]], filename: str = "data/latest_slots.json"):
        """Save slots to a JSON file"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_slots": len(slots),
                "slots": slots
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Saved {len(slots)} slots to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving slots to file: {str(e)}")
    
    @staticmethod
    def load_slots_from_file(filename: str = "data/latest_slots.json") -> List[Dict[str, Any]]:
        """Load slots from a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get("slots", [])
            
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    @staticmethod
    def save_check_history(check_result: Dict[str, Any], filename: str = "data/check_history.json"):
        """Save check history for analysis"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Load existing history
            history = []
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                history = []
            
            # Add new check result
            history.append(check_result)
            
            # Keep only last 100 check results
            history = history[-100:]
            
            # Save back to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
            
            logging.debug(f"Saved check history to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving check history: {str(e)}")
    
    @staticmethod
    def get_check_statistics(filename: str = "data/check_history.json") -> Dict[str, Any]:
        """Get statistics from check history"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                return {"total_checks": 0}
            
            total_checks = len(history)
            successful_checks = sum(1 for check in history if check.get("success", False))
            total_slots_found = sum(check.get("slots_found", 0) for check in history)
            
            # Calculate average slots per check
            avg_slots = total_slots_found / total_checks if total_checks > 0 else 0
            
            # Get success rate
            success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 0
            
            return {
                "total_checks": total_checks,
                "successful_checks": successful_checks,
                "success_rate": round(success_rate, 2),
                "total_slots_found": total_slots_found,
                "average_slots_per_check": round(avg_slots, 2)
            }
            
        except (FileNotFoundError, json.JSONDecodeError):
            return {"total_checks": 0}
