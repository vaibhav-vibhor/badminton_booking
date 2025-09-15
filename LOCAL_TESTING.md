# Local Testing Guide

## Quick Setup

1. **Create your local environment file:**
   ```powershell
   python setup_local.py
   ```

2. **Edit `.env` with your real credentials:**
   - Open `.env` file in your editor
   - Replace placeholder values with your real:
     - `PHONE_NUMBER`: Your phone number for the website login
     - `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
     - `TELEGRAM_CHAT_ID`: Your chat ID

3. **Run local test:**
   ```powershell
   python run_local_test.py
   ```

## Security Features

✅ **Your credentials are safe:**
- `.env` file is in `.gitignore` - won't be committed
- Local script masks credentials in logs
- GitHub Actions uses encrypted secrets

✅ **Dual environment support:**
- GitHub Actions: Uses environment secrets
- Local testing: Uses `.env` file
- No code changes needed between environments

## Getting Your Credentials

### 📱 Phone Number
- Use the same number you use to login to the badminton website
- Include country code (e.g., +1234567890)

### 🤖 Telegram Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Choose a name and username
4. Copy the token (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 💬 Chat ID
1. Start a conversation with your bot
2. Send any message
3. Run: `python get_chat_id.py`
4. Copy the chat ID

## Testing Options

### Full Test (Recommended)
```powershell
python run_local_test.py
```

### Original Script (Also works with .env)
```powershell
python github_actions_checker.py
```

### Debug Mode
Add to your `.env` file:
```
DEBUG_MODE=true
HEADLESS_MODE=false
```

## Troubleshooting

### "No .env file found"
Run: `python setup_local.py`

### "Missing credentials"
Edit `.env` and replace all placeholder values

### "Phone input field not found"
This should be fixed now, but if it happens:
1. Check website is accessible
2. Try with `HEADLESS_MODE=false` to see what's happening

## Example .env File
```
PHONE_NUMBER=+1234567890
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
EMAIL=your.email@example.com
DEBUG_MODE=false
HEADLESS_MODE=true
```

---

🔒 **Security**: Your `.env` file is already protected by `.gitignore` and will never be committed to the repository.
