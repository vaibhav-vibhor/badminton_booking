from github_actions_checker import GitHubActionsChecker
from dotenv import load_dotenv
load_dotenv()

checker = GitHubActionsChecker()
dates = ['2025-09-19', '2025-09-22']

# Small test to verify the legend appears
test_slots = [
    {'academy': 'Kotak', 'date': '2025-09-19', 'court': '1', 'time': '12:00-13:00'},
    {'academy': 'Pullela', 'date': '2025-09-19', 'court': '2', 'time': '19:00-20:00'},
]

message = checker.format_results_message(test_slots, dates)
print("=== Final Format with Legend ===")
print(message)

# Send final test
success = checker.send_telegram_message(message)
if success:
    print("\n✅ Final compact format with legend sent to Telegram!")
    print("📱 This is the final version that will be deployed.")
else:
    print("\n❌ Failed to send message.")
