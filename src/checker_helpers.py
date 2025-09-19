"""
GitHub Actions Checker Helper Utilities
Contains helper functions and utilities for the main checker
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent.parent / '.env'
    
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Set environment variable only if not already set
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")


def send_telegram_message(telegram_token, chat_id, message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Telegram message sent successfully")
            return True
        else:
            logger.error(f"❌ Telegram API error: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending Telegram message: {e}")
        return False


def get_check_dates():
    """Get dates to check based on configuration settings (in IST timezone)"""
    # Use IST timezone for date calculations
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist_timezone)
    
    # Load configuration
    config_path = Path(__file__).parent.parent / 'config' / 'settings.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            check_days = config.get('check_days', {
                'monday': True,
                'tuesday': False, 
                'wednesday': False,
                'thursday': False,
                'friday': True,
                'saturday': False,
                'sunday': False
            })
    except Exception as e:
        logger.warning(f"⚠️ Could not load config, using defaults: {e}")
        # Default to Friday and Monday
        check_days = {
            'monday': True,
            'tuesday': False,
            'wednesday': False, 
            'thursday': False,
            'friday': True,
            'saturday': False,
            'sunday': False
        }
    
    # Map day names to weekday numbers (Monday=0, Sunday=6)
    day_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    # Find enabled days
    enabled_days = [day_mapping[day] for day, enabled in check_days.items() if enabled]
    
    if not enabled_days:
        logger.warning("⚠️ No days enabled in config, defaulting to Friday and Monday")
        enabled_days = [4, 0]  # Friday and Monday
    
    # Calculate next occurrence of each enabled day
    upcoming_dates = {}
    
    for target_day in enabled_days:
        # Calculate days until target day
        days_until = (target_day - today.weekday()) % 7
        if days_until == 0:  # Today is the target day
            days_until = 7  # Get next occurrence instead
        
        next_date = today + timedelta(days=days_until)
        
        # Convert weekday number back to day name
        day_name = next((name for name, num in day_mapping.items() if num == target_day), str(target_day))
        
        upcoming_dates[day_name] = {
            'date': next_date.strftime('%Y-%m-%d'),
            'display': next_date.strftime('%a %b %d')
        }
    
    # Sort by date to maintain consistent order
    sorted_dates = dict(sorted(upcoming_dates.items(), key=lambda x: x[1]['date']))
    
    # Log what days we're checking
    display_names = [info['display'] for info in sorted_dates.values()]
    logger.info(f"📅 Checking dates: {' & '.join(display_names)}")
    
    return sorted_dates


def format_results_message(all_slots, dates):
    """Format the results into a beautiful Telegram message"""
    try:
        message = "🏸 *Badminton Slot Availability*\n"
        message += f"📅 *{dates['friday']['display']} & {dates['monday']['display']}*\n\n"
        
        total_available = 0
        has_available_slots = False
        
        # Process each academy
        academy_messages = []
        for academy_data in all_slots:
            academy_name = academy_data['name']
            academy_slots = academy_data['slots']
            
            # Count available slots for this academy
            academy_available = sum(len(slots['available']) for slots in academy_slots.values())
            total_available += academy_available
            
            # Determine short name for table
            academy_short = academy_name.split()[0]  # Get first word (Kotak, Pullela, SAI)
            if academy_short == "Pullela" and "SAI" in academy_name:
                academy_short = "SAI"
            
            # Create table for this academy
            if academy_available > 0:
                has_available_slots = True
                table = create_academy_table(academy_short, academy_slots)
                academy_messages.append(f"*{academy_short}* ({academy_available} slots)\n{table}")
            else:
                academy_messages.append(f"*{academy_short}* (0 slots)")
        
        # Add academy information
        if has_available_slots:
            message += "\n".join(academy_messages)
        else:
            message += "❌ *No slots currently available*"
        
        # Detect environment and add indicator
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        env_indicator = "🤖 *GitHub Actions*" if is_github_actions else "💻 *Local Run*"
        
        # Add timestamp with IST timezone
        from datetime import timezone
        ist_timezone = timezone(timedelta(hours=5, minutes=30))  # IST is UTC+5:30
        current_time_ist = datetime.now(ist_timezone).strftime('%H:%M')
        
        message += f"\n\n⚡ *Via API* - {current_time_ist} IST - {env_indicator}"
        message += "\n🔗 [Book Now](https://booking.gopichandacademy.com/)"
        
        return message
        
    except Exception as e:
        logger.error(f"❌ Error formatting results: {e}")
        return f"❌ Error formatting results: {str(e)}"


def create_academy_table(academy_short, academy_slots):
    """Create a compact table format for an academy's available slots"""
    # Define academy-specific configurations based on actual data patterns
    academy_configs = {
        'Kotak': {
            'courts': list(range(1, 7)),  # Courts 1-6
            'time_slots': ['12:00-13:00', '13:00-14:00', '18:00-19:00', '19:00-20:00', '20:00-21:00', '21:00-22:00'],
            'time_labels': ['12h', '13h', '18h', '19h', '20h', '21h']  # Compact labels
        },
        'Pullela': {
            'courts': list(range(1, 9)),  # Courts 1-8 
            'time_slots': ['12:00-13:00', '13:00-14:00', '19:00-20:00', '20:00-21:00', '21:00-22:00'],
            'time_labels': ['12h', '13h', '19h', '20h', '21h']
        },
        'SAI': {
            'courts': list(range(1, 10)),  # Courts 1-9
            'time_slots': ['12:00-13:00', '13:00-14:00', '18:00-19:00', '19:00-20:00', '20:00-21:00', '21:00-22:00'],
            'time_labels': ['12h', '13h', '18h', '19h', '20h', '21h']
        }
    }
    
    config = academy_configs.get(academy_short, academy_configs['SAI'])  # Default to SAI config
    
    # Create availability matrix - check all dates
    availability_matrix = {}
    for court in config['courts']:
        availability_matrix[court] = {}
        for time_slot in config['time_slots']:
            availability_matrix[court][time_slot] = False  # Default: not available
    
    # Mark available slots from API data
    for date, date_data in academy_slots.items():
        for slot in date_data.get('available', []):
            court = slot.get('court_number')
            time_range = slot.get('time')
            
            if court in availability_matrix and time_range in availability_matrix[court]:
                availability_matrix[court][time_range] = True
    
    # Build ASCII table
    lines = []
    
    # Header row with time labels
    header = "```\n   " + " ".join(f"{label:>3}" for label in config['time_labels'])
    lines.append(header)
    
    # Court rows
    for court in config['courts']:
        row_data = []
        for time_slot in config['time_slots']:
            if availability_matrix[court][time_slot]:
                row_data.append(" ✓ ")  # Available (with padding for alignment)
            else:
                row_data.append(" • ")  # Not available (with padding for alignment)
        
        court_row = f"C{court}" + "".join(row_data)
        lines.append(court_row)
    
    lines.append("```")
    
    return "\n".join(lines)
