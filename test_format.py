from github_actions_checker import GitHubActionsChecker
from datetime import datetime
import os

# Set required env vars for the class
os.environ['PHONE_NUMBER'] = 'dummy'
os.environ['TELEGRAM_BOT_TOKEN'] = 'dummy'  
os.environ['TELEGRAM_CHAT_ID'] = 'dummy'

checker = GitHubActionsChecker()
dates = ['2025-09-19', '2025-09-22']

# Test case 1: Slots only for Friday (like your actual output)
friday_slots = [
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '13:00-14:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '2', 'time': '12:00-13:00'},
]

message = checker.format_results_message(friday_slots, dates)
print("=== Test Case: Friday slots only ===")
print(message)
print("\n" + "="*50 + "\n")

# Test case 2: No slots at all
no_slots = []
message2 = checker.format_results_message(no_slots, dates)
print("=== Test Case: No slots at all ===")
print(message2)
