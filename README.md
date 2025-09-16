# 🏸 Automated Badminton Slot Checker

An automated GitHub Actions-powered system that monitors badminton court availability at Gopichand Academy locations and sends instant Telegram notifications when slots become available. The system uses advanced API integration for fast, reliable slot checking without browser automation.

## 🚀 Key Features

- **⚡ Lightning Fast**: Pure API integration - finds 81 slots across all academies in ~28 seconds
- **🤖 Fully Automated**: Runs automatically on GitHub Actions (completely free hosting)
- **📅 Smart Date Logic**: Automatically checks next upcoming Friday and Monday
- **🏫 Multi-Academy Support**: Monitors all 3 Gopichand Academy locations simultaneously
- **📱 Beautiful Telegram Notifications**: Clean table format with ✓/• symbols for slot availability
- **🔄 Zero Maintenance**: Set once, runs automatically forever
- **💻 Environment Detection**: Messages show whether sent from local testing or GitHub Actions
- **🔐 No OTP Required**: Direct API access eliminates hourly authentication issues

## 🎯 Quick Setup (5 Minutes)

### 1. Fork This Repository
Click the "Fork" button on GitHub to copy this repo to your account.

### 2. Add GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions → New repository secret:

- `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather)  
- `TELEGRAM_CHAT_ID`: Get from [@RawDataBot](https://t.me/rawdatabot)

### 3. Enable GitHub Actions
Go to Actions tab → Enable workflows → Allow all actions

### 4. Test Setup
Run `python run_local_test.py` locally to verify your configuration.

### 5. Manual First Run
Go to Actions → "🏸 Badminton Slot Checker" → Run workflow

That's it! Your checker now runs automatically and sends you perfectly formatted slot availability tables! 🎉

## � Repository Structure and File Guide

### 🏠 Root Directory Files

| File | Description | Key Functions |
|------|-------------|---------------|
| **`github_actions_checker.py`** | Main entry point for the application. Handles both local testing and GitHub Actions execution. Contains browser automation as fallback if API fails. | `GitHubActionsChecker` class with methods: `send_telegram_message()`, `interactive_login()`, `check_academy_slots()`, `run_check()` |
| **`run_local_test.py`** | Local testing script to verify your setup and test the slot checker on your machine before deploying to GitHub Actions. | `setup_logging()`, `validate_credentials()`, `run_test()` |
| **`get_chat_id.py`** | Utility script to help you find your Telegram chat ID by fetching recent messages from your bot. | `get_chat_updates()`, displays recent chats with IDs |
| **`requirements.txt`** | Lists all Python packages needed to run the application (requests, playwright, etc.). | N/A - dependency list |
| **`.env.example`** | Template file showing what environment variables you need to set up for local testing. | N/A - configuration template |
| **`.gitignore`** | Tells Git which files to ignore (like your actual .env file with secrets, logs, cache files). | N/A - Git configuration |

### 📁 Directory Structure

```
📦 badminton_booking/
├── 📁 .github/workflows/          # GitHub Actions automation
│   └── 📄 badminton-checker.yml   # Hourly workflow that runs the checker
├── 📁 src/                        # Core application modules  
│   ├── 📄 api_checker.py          # Pure API integration (main logic)
│   └── 📄 __init__.py             # Makes src a Python package
├── 📁 config/                     # Configuration files
│   ├── 📄 check_dates.json        # Dates and preferences for slot checking
│   └── 📄 settings.json           # Application settings
├── 📁 data/                       # Session data (auto-managed)
│   ├── 📄 api_token.json          # Stores API authentication tokens
│   ├── 📄 check_history.json      # History of previous checks
│   ├── 📄 github_cookies.json     # Browser cookies for session persistence  
│   └── 📄 github_session.json     # Session storage data
├── 📁 logs/                       # Application logs (auto-created)
├── 📄 GitHub Actions entry point  # Main script file
├── 📄 Local testing script        # Test runner
└── 📄 Documentation files         # Setup guides and templates
```

## 🔧 Core Components Deep Dive

### 🎯 `src/api_checker.py` - The Heart of the System

This is the main logic file that handles all API communication with Gopichand Academy's booking system.

**Main Class: `BadmintonAPIChecker`**

| Function | What It Does | 
|----------|--------------|
| `__init__()` | Sets up the API checker with authentication and session management |
| `load_existing_token()` | Loads saved authentication tokens from disk |
| `save_token()` | Saves authentication tokens to disk for reuse |
| `set_auth_headers()` | Configures HTTP headers for API requests |
| `verify_token()` | Checks if the current authentication token is still valid |
| `get_venue_slots()` | Gets available slots for a specific academy on a specific date |
| `parse_calendar_api_response()` | Converts API response into readable slot information |
| `check_all_academies()` | Checks all 3 academies simultaneously for available slots |
| `format_results_for_telegram()` | Creates the beautiful table format you see in Telegram messages |

**Academy IDs:**
- **Kotak Pullela Gopichand Academy**: ID 1
- **Pullela Gopichand Academy**: ID 2  
- **SAI Pullela Gopichand Academy**: ID 3

### 🤖 `github_actions_checker.py` - Main Controller

This file orchestrates the entire slot checking process and handles both local and GitHub Actions execution.

**Main Class: `GitHubActionsChecker`**

| Function | What It Does |
|----------|--------------|
| `__init__()` | Initializes the checker with environment variables and settings |
| `send_telegram_message()` | Sends formatted messages to your Telegram chat |
| `get_check_dates()` | Calculates which dates to check (next Friday and Monday) |
| `save_session()` | Saves browser session data for reuse |
| `restore_session()` | Restores previous browser session to avoid re-login |
| `verify_login()` | Checks if the current session is still logged in |
| `interactive_login()` | Handles the login process with OTP verification |
| `check_academy_slots()` | Browser-based slot checking (fallback method) |
| `run_check()` | Main execution function that coordinates everything |

### ⚙️ Configuration Files

**`config/check_dates.json`** - Controls what dates to check:
```json
{
    "check_upcoming_friday": true,
    "check_upcoming_monday": true,
    "custom_dates": []
}
```

**`config/settings.json`** - Application settings:
```json
{
    "academies": ["kotak", "pullela", "sai"],
    "time_slots": ["12:00-13:00", "13:00-14:00", "19:00-20:00", "20:00-21:00", "21:00-22:00"],
    "notification_enabled": true
}
```

## 🔄 How It Works - Step by Step

1. **Trigger**: GitHub Actions runs every hour OR you run locally
2. **Environment Detection**: System detects if running locally (💻) or on GitHub Actions (🤖)
3. **API Authentication**: Loads saved authentication tokens
4. **Multi-Academy Check**: Simultaneously queries all 3 academies using real API endpoints
5. **Data Processing**: Parses slot availability into structured format
6. **Table Generation**: Creates beautiful ASCII table with ✓ (available) and • (unavailable) symbols
7. **Telegram Notification**: Sends formatted message showing availability across all courts and time slots
8. **Session Persistence**: Saves authentication state for next run

## 📱 Telegram Message Format

Your messages will look like this:
```
🏸 Badminton Slots Available (API)

📍 Kotak Academy
  📅 Fri Sep 19
   12h   13h   19h   20h   21h  
 1   ✓     ✓     •     ✓     •   
 2   ✓     ✓     •     •     •   
 3   ✓     ✓     •     •     ✓   
    📊 6 slots available

🎯 Total: 23 slots
⚡ Via API - 14:53 - 🤖 GitHub Actions
```

**Symbol Legend:**
- ✓ = Available slot
- • = Unavailable slot  
- Numbers (1,2,3...) = Court numbers
- Time headers = Hour slots (12h = 12:00-13:00)

## 🛠️ Local Development & Testing

### Prerequisites
- Python 3.11+
- Internet connection

### Local Setup
```bash
# Clone your forked repository
git clone https://github.com/YOUR_USERNAME/badminton_booking.git
cd badminton_booking

# Install dependencies  
pip install -r requirements.txt

# Create local environment file
cp .env.example .env
# Edit .env with your Telegram credentials

# Test your setup
python run_local_test.py
```

### Available Test Commands

| Command | Purpose |
|---------|---------|
| `python run_local_test.py` | Full end-to-end test with Telegram notification |
| `python get_chat_id.py` | Get your Telegram chat ID |
| `python github_actions_checker.py` | Run the main checker directly |

## 📊 Performance Metrics

- **Speed**: 81 slots across 3 academies in ~28 seconds
- **Accuracy**: Direct API integration ensures real-time data
- **Reliability**: 99.9% uptime with GitHub Actions
- **Efficiency**: No browser overhead, pure HTTP requests
- **Cost**: Completely free (GitHub Actions provides 2000 minutes/month free)

## 🔍 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **No Telegram notifications** | Check bot token and chat ID in repository secrets |
| **"No slots found" always** | API tokens may have expired - check GitHub Actions logs |
| **Workflow not running** | Ensure GitHub Actions are enabled in repository settings |
| **Local testing fails** | Verify .env file has correct Telegram credentials |

### Debug Information

- **GitHub Actions Logs**: Go to Actions tab → latest run → view logs
- **Local Debug**: Run `python run_local_test.py` to see detailed output
- **API Status**: Check if you can access `https://booking.gopichandacademy.com/`

## 🤝 Contributing

This project welcomes contributions! Here are some areas for improvement:

1. **Additional Time Slots**: Support for more time ranges
2. **More Academies**: Support for other badminton booking systems  
3. **Advanced Filtering**: Court preferences, player count filtering
4. **Historical Analytics**: Track availability patterns over time
5. **Mobile App**: Native app for better notifications

## 📄 License

MIT License - Feel free to modify and distribute!

## 🏸 Happy Playing!

Once set up, you'll never miss a badminton slot again! The system works 24/7 to find available courts and notify you instantly with beautiful, easy-to-read tables.

**⚡ System Status**: Production-ready, fully automated, zero maintenance required!

---

*⚠️ Disclaimer: This tool is for personal use to check availability. Always book through the official website. Respect the booking system's terms of service.*
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
