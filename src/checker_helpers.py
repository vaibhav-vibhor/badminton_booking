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
    """Get the next Friday and Monday dates to check (in IST timezone)"""
    # Use IST timezone for date calculations
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist_timezone)
    
    # Find next Friday (weekday 4, where Monday=0)
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:  # Today is Friday
        days_until_friday = 7  # Get next Friday instead
    
    next_friday = today + timedelta(days=days_until_friday)
    
    # Find next Monday after that Friday (3 days after Friday)
    # Friday -> Saturday (1 day) -> Sunday (2 days) -> Monday (3 days)
    next_monday = next_friday + timedelta(days=3)
    
    # Format dates for API calls (without timezone info)
    friday_str = next_friday.strftime('%Y-%m-%d')
    monday_str = next_monday.strftime('%Y-%m-%d')
    
    # Format for display
    friday_display = next_friday.strftime('%a %b %d')
    monday_display = next_monday.strftime('%a %b %d')
    
    logger.info(f"📅 Checking dates: {friday_display} & {monday_display}")
    
    return {
        'friday': {'date': friday_str, 'display': friday_display},
        'monday': {'date': monday_str, 'display': monday_display}
    }


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
