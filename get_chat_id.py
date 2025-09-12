import requests
from dotenv import load_dotenv
import os

load_dotenv()
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

print('📋 Getting chat updates to find your correct chat ID...')
url = f'https://api.telegram.org/bot{bot_token}/getUpdates'
response = requests.get(url, timeout=10)

if response.status_code == 200:
    data = response.json()
    if data['result']:
        print('Recent chats:')
        for update in data['result'][-5:]:  # Show last 5 updates
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                first_name = update['message']['chat'].get('first_name', 'Unknown')
                text = update['message'].get('text', '')[:50]
                print(f'  Chat ID: {chat_id} - {first_name} - "{text}"')
        
        # Get the most recent chat ID
        if data['result']:
            latest_update = data['result'][-1]
            if 'message' in latest_update:
                correct_chat_id = latest_update['message']['chat']['id']
                print(f'\n✅ Your correct chat ID is: {correct_chat_id}')
                
                # Test sending a message with the correct chat ID
                print('\n🧪 Testing message send with correct chat ID...')
                send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                test_response = requests.post(send_url, json={
                    'chat_id': correct_chat_id,
                    'text': '🎉 Success! Your Badminton Checker is working!'
                }, timeout=10)
                
                if test_response.status_code == 200:
                    print('✅ Message sent successfully!')
                    print(f'\nUpdate your .env file with: TELEGRAM_CHAT_ID={correct_chat_id}')
                else:
                    print(f'❌ Message failed: {test_response.text}')
    else:
        print('❌ No messages found. Please send a message to @pullelabot first!')
        print('1. Open Telegram')
        print('2. Search for @pullelabot')
        print('3. Send any message (like "hello")')
        print('4. Run this script again')
else:
    print(f'Error getting updates: {response.text}')
