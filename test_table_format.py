from github_actions_checker import GitHubActionsChecker
import os

# Set required env vars for the class
os.environ['PHONE_NUMBER'] = 'dummy'
os.environ['TELEGRAM_BOT_TOKEN'] = 'dummy'  
os.environ['TELEGRAM_CHAT_ID'] = 'dummy'

checker = GitHubActionsChecker()
dates = ['2025-09-19', '2025-09-22']

# Create test slots based on your actual data
test_slots = [
    # Kotak slots
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '13:00-14:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '20:00-21:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '2', 'time': '12:00-13:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '3', 'time': '19:00-20:00'},
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '4', 'time': '18:00-19:00'},
    
    # Pullela slots
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '2', 'time': '20:00-21:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '8', 'time': '19:00-20:00'},
    
    # SAI slots
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '1', 'time': '19:00-20:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '2', 'time': '20:00-21:00'},
    {'academy': 'SAI', 'date': '2025-09-19', 'court': '9', 'time': '21:00-22:00'},
]

message = checker.format_results_message(test_slots, dates)
print("=== Table Format Test ===")
print(message)
print("\n" + "="*60 + "\n")

# Test with no slots
no_slots = []
message2 = checker.format_results_message(no_slots, dates)
print("=== No Slots Test ===")
print(message2)
