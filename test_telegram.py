import requests
import os
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

print('🔍 Testing Telegram Bot Configuration...')
print(f'Bot Token: {bot_token[:10] if bot_token else "Not found"}...{bot_token[-10:] if bot_token and len(bot_token) > 20 else ""}')
print(f'Chat ID: {chat_id}')

if bot_token:
    # Test bot info
    url = f'https://api.telegram.org/bot{bot_token}/getMe'
    try:
        response = requests.get(url)
        print(f'Bot API Response: {response.status_code}')
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f'✅ Bot is valid: @{bot_info["result"]["username"]}')
            
            # Test sending message
            if chat_id:
                send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                test_message = '🧪 Test message from Badminton Checker!'
                send_response = requests.post(send_url, json={
                    'chat_id': chat_id,
                    'text': test_message
                })
                print(f'Message send status: {send_response.status_code}')
                if send_response.status_code == 200:
                    print('✅ Telegram integration working!')
                else:
                    print(f'❌ Message failed: {send_response.text}')
        else:
            print(f'❌ Bot token invalid: {response.text}')
    except Exception as e:
        print(f'❌ Error testing bot: {e}')
else:
    print('❌ No bot token found in .env file')
