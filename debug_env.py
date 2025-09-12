import os

print('=== Environment Variables Debug ===')
print(f'PHONE_NUMBER: {os.environ.get("PHONE_NUMBER", "Not found")}')
print(f'TELEGRAM_BOT_TOKEN: {os.environ.get("TELEGRAM_BOT_TOKEN", "Not found")}')
print(f'TELEGRAM_CHAT_ID: {os.environ.get("TELEGRAM_CHAT_ID", "Not found")}')

print('\n=== .env file contents ===')
try:
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
except Exception as e:
    print(f'Error reading .env: {e}')

print('\n=== Testing dotenv loading ===')
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f'After load_dotenv - PHONE_NUMBER: {os.environ.get("PHONE_NUMBER", "Still not found")}')
    print(f'After load_dotenv - TELEGRAM_BOT_TOKEN: {os.environ.get("TELEGRAM_BOT_TOKEN", "Still not found")}')
    print(f'After load_dotenv - TELEGRAM_CHAT_ID: {os.environ.get("TELEGRAM_CHAT_ID", "Still not found")}')
except Exception as e:
    print(f'Error with dotenv: {e}')
