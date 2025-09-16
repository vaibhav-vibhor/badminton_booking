from github_actions_checker import GitHubActionsChecker
import os
from dotenv import load_dotenv
load_dotenv()

# Set required env vars for the class
os.environ['PHONE_NUMBER'] = 'dummy'
os.environ['TELEGRAM_BOT_TOKEN'] = 'dummy'  
os.environ['TELEGRAM_CHAT_ID'] = 'dummy'

checker = GitHubActionsChecker()
dates = ['2025-09-19', '2025-09-22']

# Create test slots to test the compact format
test_slots = [
    # Kotak slots - test all time slots
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '13:00-14:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '20:00-21:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '2', 'time': '12:00-13:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '3', 'time': '19:00-20:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '4', 'time': '18:00-19:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '6', 'time': '21:00-22:00'},
    
    # Pullela slots
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '2', 'time': '20:00-21:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '8', 'time': '19:00-20:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '4', 'time': '21:00-22:00'},
    
    # SAI slots  
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '1', 'time': '19:00-20:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '9', 'time': '21:00-22:00'},
]

message = checker.format_results_message(test_slots, dates)
print("=== Compact Table Format Test ===")
print(message)
print("\n" + "="*50)
print(f"Message length: {len(message)} characters")
print("="*50)

# Check each line length to see if it fits better
lines = message.split('\n')
max_line_length = 0
for i, line in enumerate(lines):
    if '`' in line:  # Table lines
        print(f"Table line {i}: '{line}' (length: {len(line)})")
        max_line_length = max(max_line_length, len(line))

print(f"\nMax table line length: {max_line_length} characters")
print("Telegram typically handles ~40-45 characters well for monospace text.")
