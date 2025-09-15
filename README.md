# 🏸 Automated Badminton Slot Checker

An automated GitHub Actions-powered system that monitors badminton court availability at Gopichand Academy locations every hour and sends instant Telegram notifications when slots become available on upcoming Fridays and Mondays.

## 🚀 Key Features

- **🤖 Fully Automated**: Runs every hour on GitHub Actions (completely free hosting)
- **📅 Smart Date Logic**: Automatically checks next upcoming Friday and Monday only
- **🏫 Multi-Academy Support**: Monitors all Gopichand Academy locations
- **💾 Session Persistence**: Maintains login between automated runs
- **📱 Instant Notifications**: Real-time Telegram alerts with slot details
- **🔄 Headless Operation**: Runs invisibly on GitHub servers
- **⚡ Zero Maintenance**: Set once, runs automatically forever

## 🎯 Quick Setup (5 Minutes)

### 1. Fork This Repository
Click the "Fork" button on GitHub to copy this repo to your account.

### 2. Add GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions → New repository secret:

- `PHONE_NUMBER`: Your phone number with country code (e.g., +1234567890)
- `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather)  
- `TELEGRAM_CHAT_ID`: Get from [@RawDataBot](https://t.me/rawdatabot)

### 3. Enable GitHub Actions
Go to Actions tab → Enable workflows → Allow all actions

### 4. Test Setup
Run `python test_github_setup.py` locally to verify your configuration.

### 5. Manual First Run
Go to Actions → "🏸 Badminton Slot Checker" → Run workflow

That's it! Your checker now runs automatically every hour! 🎉

## 📁 Project Structure

```
badminton_booking/
├── .github/workflows/          # GitHub Actions automation
│   └── badminton-checker.yml   # Hourly workflow definition
├── src/                        # Core application modules
│   ├── main.py                 # Main checker logic
│   ├── login_handler.py        # Login and session management
│   ├── booking_checker.py      # Slot availability checking
│   ├── notification_handler.py # Telegram notifications
│   └── ...                     # Other core modules
├── config/                     # Configuration files
├── data/                       # Session data (auto-managed)
├── logs/                       # Application logs
├── github_actions_checker.py   # GitHub Actions entry point
├── test_github_setup.py        # Setup verification tool
├── get_chat_id.py             # Utility to find Telegram chat ID
├── requirements.txt            # Python dependencies
├── GITHUB_ACTIONS_SETUP.md     # Detailed setup guide
└── README.md                   # This file
```

## 🛠️ Setup Instructions

### Step 1: Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to create your bot
4. Save the **Bot Token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Start a chat with your new bot and send any message
6. Get your Chat ID by visiting: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
7. Find your **Chat ID** in the response (looks like `123456789`)

### Step 2: Fork and Configure Repository

1. **Fork this repository** to your GitHub account
2. Go to your forked repository
3. Navigate to **Settings** → **Secrets and variables** → **Actions**
4. Click **New repository secret** and add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `PHONE_NUMBER` | Your registered phone number | `9876543210` |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | `123456789:ABCdef...` |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | `123456789` |

### Step 3: Configure Dates and Preferences

1. Edit `config/check_dates.json` in your repository:

```json
{
    "dates_to_check": [
        "2025-09-13",
        "2025-09-14", 
        "2025-09-15"
    ],
    "time_preferences": {
        "preferred": [
            "18:00-19:00",
            "19:00-20:00", 
            "20:00-21:00"
        ],
        "acceptable": [
            "17:00-18:00",
            "21:00-22:00"
        ],
        "notify_all": false
    },
    "court_preferences": {
        "preferred_courts": [1, 2, 3, 4, 5],
        "check_all_courts": true
    },
    "academies_to_check": ["kotak", "pullela", "sai"],
    "notification_settings": {
        "notify_immediately": true,
        "batch_notifications": false,
        "max_notifications_per_run": 10
    }
}
```

## 🔧 Local Development & Testing

### Prerequisites
- Python 3.11+
- Registered phone number with Gopichand Academy

### Local Setup
```bash
# Clone your forked repository
git clone https://github.com/YOUR_USERNAME/badminton_booking.git
cd badminton_booking

# Install dependencies  
pip install -r requirements.txt
playwright install chromium

# Create local environment file
cp .env.example .env
# Edit .env with your credentials

# Test your setup
python test_github_setup.py

# Run a local test
python github_actions_checker.py
```

## 📱 How It Works

1. **Automated Schedule**: GitHub Actions runs the checker every hour
2. **Session Management**: Maintains login cookies between runs using GitHub artifacts
3. **Smart Date Logic**: Always checks the next upcoming Friday and Monday
4. **Multi-Academy Check**: Simultaneously monitors all Gopichand Academy locations
5. **Instant Alerts**: Sends detailed Telegram messages with available slot information
6. **Error Recovery**: Handles login failures, network issues, and session expiration

## 🔍 Available Utilities

### Test Your Setup
```bash
python test_github_setup.py
```
Verifies all environment variables and connections.

### Get Your Telegram Chat ID  
```bash
python get_chat_id.py
```
Interactive tool to find your Telegram chat ID.

## 📊 Monitoring & Logs

- **GitHub Actions Logs**: View execution details in the Actions tab
- **Telegram Notifications**: Get real-time updates on your phone
- **Session Persistence**: Automatic session management between runs
- **Error Alerts**: Notification of any system failures

## 🔧 Troubleshooting

### Common Issues
1. **No notifications**: Check your Telegram bot token and chat ID
2. **Login failures**: GitHub Actions may need a fresh session (run manually once)
3. **Missing slots**: Verify your phone number is registered with the academy
4. **Workflow disabled**: Ensure GitHub Actions are enabled in your repository

### Getting Help
- Check `GITHUB_ACTIONS_SETUP.md` for detailed setup instructions  
- Review GitHub Actions logs for error details
- Test locally with `python test_github_setup.py`

## 📄 License

MIT License - Feel free to modify and distribute!

## 🙏 Contributing

---

**� Happy badminton booking! May you always find your perfect court time! 🏸**
- Weekly summary notifications

## 🚨 Rate Limiting and Best Practices

The system implements smart rate limiting:
- **2 second delay** between requests
- **5 second delay** between academies  
- **1 second delay** between courts
- **15 minute interval** between full checks

**Important:** 
- Don't reduce delays too much (risk of being blocked)
- Don't run multiple instances simultaneously  
- Respect the booking website's terms of service

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

1. **OTP Automation**: SMS API integration or email parsing
2. **Additional Academies**: Support for other booking systems
3. **Web Dashboard**: Visual interface for configuration
4. **Smart Scheduling**: ML-based optimal check timing
5. **Mobile App**: Native mobile notifications

## � Recent Updates & Fixes

### ✅ SPA Login Issue Fixed (September 2025)

**Problem**: The automation was failing with "phone input field not found" because the website uses a Single Page Application (SPA) with modal-based login.

**Root Cause**: The script was trying to navigate to `/login` (which returns 404) instead of using the modal overlay system.

**Solution Implemented**:
1. **Navigate to main page**: `https://booking.gopichandacademy.com/` (not `/login`)
2. **Click "Login / SignUp" button**: Opens modal overlay on same page
3. **Wait for modal**: Look for `.modal-overlay` element
4. **Find mobile input**: Use `#mobile` selector within modal context
5. **Find OTP button**: Use `input[value="Send OTP"]` within modal

**Key Changes**:
- Updated `interactive_login()` to handle modal-based authentication
- Added modal-specific selectors for phone input and OTP button
- Enhanced debugging with modal content analysis
- Added proper wait conditions for dynamic content loading

If you're still experiencing issues, ensure you're using the latest version of the script.

## �📄 License

This project is for educational purposes. Please respect the terms of service of the booking website and use responsibly.

## 🙋‍♂️ Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review GitHub Actions logs for error details
3. Create an issue in this repository with:
   - Error messages from logs
   - Your configuration (without credentials)
   - Steps to reproduce the problem

## 🏸 Happy Playing!

Once set up, you'll never miss a badminton slot again! The system works 24/7 to find available courts and notify you instantly via Telegram.

---

**⚠️ Disclaimer**: This tool is for personal use to check availability. Always book through the official website. Respect the booking system's terms of service and don't attempt to automate actual bookings.
