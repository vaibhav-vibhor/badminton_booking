from github_actions_checker import GitHubActionsChecker
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

checker = GitHubActionsChecker()
dates = ['2025-09-19', '2025-09-22']

# Create test slots similar to your real data
test_slots = [
    # Kotak slots - representative sample
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '13:00-14:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '20:00-21:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '2', 'time': '12:00-13:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '3', 'time': '19:00-20:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '4', 'time': '18:00-19:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '6', 'time': '20:00-21:00'},
    
    # Pullela slots - representative sample
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '2', 'time': '20:00-21:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '3', 'time': '19:00-20:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '8', 'time': '19:00-20:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '4', 'time': '21:00-22:00'},
    
    # SAI slots - representative sample  
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '1', 'time': '19:00-20:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '2', 'time': '20:00-21:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '3', 'time': '19:00-20:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '7', 'time': '19:00-20:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '8', 'time': '21:00-22:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '9', 'time': '21:00-22:00'},
]

message = checker.format_results_message(test_slots, dates)
print("Sending test message with new table format...")
print("="*60)
print(message)
print("="*60)

# Send the test message
success = checker.send_telegram_message(message)
if success:
    print("✅ Test message sent successfully to Telegram!")
    print("Check your Telegram chat to see how the tables look.")
else:
    print("❌ Failed to send test message to Telegram.")
