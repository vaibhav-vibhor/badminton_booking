from github_actions_checker import GitHubActionsChecker
from datetime import datetime, timedelta
import os

# Set required env vars for the class
os.environ['PHONE_NUMBER'] = 'dummy'
os.environ['TELEGRAM_BOT_TOKEN'] = 'dummy'  
os.environ['TELEGRAM_CHAT_ID'] = 'dummy'

checker = GitHubActionsChecker()
dates = checker.get_check_dates()
print('Dates to check:', dates)

for date in dates:
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    print(f'{date} -> {date_obj.strftime("%A, %B %d")}')

# Also show what today is
today = datetime.now()
print(f'\nToday is: {today.strftime("%A, %B %d, %Y")}')
